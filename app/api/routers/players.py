"""Игроки: поиск и фильтры (требование 1)."""
from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db_rls
from app.models import Player, Team
from app.schemas import PlayerListOut

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=List[PlayerListOut])
def list_players(
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
