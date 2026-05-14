"""Игроки: поиск, карточка, смена команды (admin), роль, сравнение с бенчмарком, программа."""
from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.ai.analyzer import recommend_exercises_for_player
from app.api.deps import CurrentUser, get_current_user, get_db_rls, require_roles
from app.models import Player, Team
from app.schemas import (
    ClusterRoleRow,
    PeerComparisonResponse,
    PeerMetricRow,
    PlayerListOut,
    PlayerTeamUpdate,
    RoleProfileResponse,
    TrainingProgramRequest,
    TrainingProgramResponse,
)
from app.services.player_analysis import get_peer_comparison, get_role_profile

router = APIRouter(prefix="/players", tags=["players"])

_coach_or_admin = require_roles("coach", "admin")
_admin_only = require_roles("admin")


@router.get("", response_model=List[PlayerListOut])
def list_players(
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
    q: Annotated[Optional[str], Query(description="Подстрока в имени игрока")] = None,
    team_id: Annotated[Optional[int], Query()] = None,
    league_id: Annotated[Optional[int], Query()] = None,
    position: Annotated[Optional[str], Query(description="Амплуа (position)")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> List[Player]:
    query = db.query(Player).options(joinedload(Player.team))
    query = query.outerjoin(Team, Player.team_id == Team.team_id)
    if q:
        query = query.filter(Player.player_name.ilike(f"%{q}%"))
    if team_id is not None:
        query = query.filter(Player.team_id == team_id)
    if league_id is not None:
        query = query.filter(Team.league_id == league_id)
    if position:
        query = query.filter(Player.position.ilike(position.strip()))
    return (
        query.order_by(Player.player_name)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.post(
    "/{player_id}/training-programs",
    response_model=TrainingProgramResponse,
)
def create_training_program(
    player_id: int,
    body: TrainingProgramRequest,
    user: Annotated[CurrentUser, Depends(_coach_or_admin)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> TrainingProgramResponse:
    result = recommend_exercises_for_player(
        player_id=player_id,
        user_id=user.user_id,
        user_login=user.user_login,
        season_year=body.season_start_year,
        db=db,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Ошибка анализа"),
        )
    return TrainingProgramResponse.model_validate(result)


@router.get("/{player_id}/role-profile", response_model=RoleProfileResponse)
def role_profile(
    player_id: int,
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> RoleProfileResponse:
    data = get_role_profile(db, player_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Игрок не найден"
        )
    analyses = [ClusterRoleRow(**a) for a in data["analyses"]]
    primary = (
        ClusterRoleRow(**data["primary_role"])
        if data.get("primary_role")
        else None
    )
    return RoleProfileResponse(
        player_id=data["player_id"],
        player_name=data["player_name"],
        primary_role=primary,
        analyses=analyses,
    )


@router.get("/{player_id}/peer-comparison", response_model=PeerComparisonResponse)
def peer_comparison(
    player_id: int,
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
    season_start_year: Annotated[
        Optional[int], Query(description="Год начала сезона; по умолчанию — последний у игрока")
    ] = None,
) -> PeerComparisonResponse:
    data = get_peer_comparison(db, player_id, season_start_year)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Игрок не найден"
        )
    metrics = [PeerMetricRow(**m) for m in data["metrics"]]
    return PeerComparisonResponse(
        player_id=data["player_id"],
        player_name=data["player_name"],
        role_id=data.get("role_id"),
        role_name=data.get("role_name"),
        league_id=data.get("league_id"),
        season_start_year=data.get("season_start_year"),
        error=data.get("error"),
        metrics=metrics,
    )


@router.get("/{player_id}", response_model=PlayerListOut)
def get_player(
    player_id: int,
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> Player:
    p = (
        db.query(Player)
        .options(joinedload(Player.team))
        .filter(Player.player_id == player_id)
        .first()
    )
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Игрок не найден"
        )
    return p


@router.patch("/{player_id}", response_model=PlayerListOut)
def update_player_team(
    player_id: int,
    body: PlayerTeamUpdate,
    _admin: Annotated[CurrentUser, Depends(_admin_only)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> Player:
    p = (
        db.query(Player)
        .options(joinedload(Player.team))
        .filter(Player.player_id == player_id)
        .first()
    )
    if p is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Игрок не найден"
        )
    p.team_id = body.team_id
    db.flush()
    return p
