"""Роль игрока (кластер) и сравнение с бенчмарком роли в лиге (Z-score)."""
from __future__ import annotations

from typing import Any, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import Benchmark, ClusterAnalysis, Player, SeasonMetric


def get_role_profile(db: Session, player_id: int) -> Optional[dict[str, Any]]:
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        return None
    rows = (
        db.query(ClusterAnalysis)
        .options(joinedload(ClusterAnalysis.roles))
        .filter(ClusterAnalysis.player_id == player_id)
        .order_by(ClusterAnalysis.trust_score.desc().nulls_last())
        .all()
    )
    analyses: List[dict[str, Any]] = []
    for ca in rows:
        r = ca.roles
        analyses.append(
            {
                "analysis_id": ca.analysis_id,
                "role_id": ca.role_id,
                "role_name": r.role_name if r else None,
                "zone": r.zone if r else None,
                "trust_score": float(ca.trust_score) if ca.trust_score is not None else None,
            }
        )
    return {
        "player_id": player.player_id,
        "player_name": player.player_name,
        "primary_role": analyses[0] if analyses else None,
        "analyses": analyses,
    }


def _resolve_season_year(db: Session, player_id: int, season_start_year: Optional[int]) -> Optional[int]:
    if season_start_year is not None:
        return season_start_year
    y = (
        db.query(func.max(SeasonMetric.season_start_year))
        .filter(SeasonMetric.player_id == player_id)
        .scalar()
    )
    return int(y) if y is not None else None


def get_peer_comparison(
    db: Session, player_id: int, season_start_year: Optional[int] = None
) -> Optional[dict[str, Any]]:
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        return None
    cluster = (
        db.query(ClusterAnalysis)
        .options(joinedload(ClusterAnalysis.roles))
        .filter(ClusterAnalysis.player_id == player_id)
        .order_by(ClusterAnalysis.trust_score.desc())
        .first()
    )
    if not cluster:
        return {
            "player_id": player.player_id,
            "player_name": player.player_name,
            "error": "Нет кластерного анализа для игрока",
            "metrics": [],
        }
    league_id = player.team.league_id if player.team else None
    if not league_id:
        return {
            "player_id": player.player_id,
            "player_name": player.player_name,
            "error": "Лига не определена для игрока",
            "metrics": [],
        }
    role = cluster.roles
    season_y = _resolve_season_year(db, player_id, season_start_year)

    q = db.query(SeasonMetric).filter(SeasonMetric.player_id == player_id)
    if season_y is not None:
        q = q.filter(SeasonMetric.season_start_year == season_y)
    season_metrics = q.all()

    metrics_out: List[dict[str, Any]] = []
    for sm in season_metrics:
        m = sm.metric
        actual = float(sm.season_metric_value) if sm.season_metric_value is not None else 0.0
        bench = (
            db.query(Benchmark)
            .filter(
                Benchmark.metric_id == m.metric_id,
                Benchmark.role_id == cluster.role_id,
                Benchmark.league_id == league_id,
            )
            .first()
        )
        if not bench or not bench.standard_deviation or float(bench.standard_deviation) == 0:
            continue
        std = float(bench.standard_deviation)
        mean = float(bench.mean)
        z = (actual - mean) / std
        metrics_out.append(
            {
                "metric_id": m.metric_id,
                "metric_name": m.metric_name,
                "season_start_year": sm.season_start_year,
                "value": actual,
                "benchmark_mean": mean,
                "benchmark_std": std,
                "z_score": round(z, 3),
            }
        )

    metrics_out.sort(key=lambda x: x["z_score"])

    return {
        "player_id": player.player_id,
        "player_name": player.player_name,
        "role_id": role.role_id if role else None,
        "role_name": role.role_name if role else None,
        "league_id": league_id,
        "season_start_year": season_y,
        "metrics": metrics_out,
    }
