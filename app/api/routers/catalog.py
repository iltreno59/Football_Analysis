"""Справочники: лиги, клубы, тактические роли (требование — просмотр всеми)."""
from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_rls
from app.models import League, Roles, Team
from app.schemas import League as LeagueSchema, Roles as RolesSchema, Team as TeamSchema

router = APIRouter(tags=["catalog"])


@router.get("/leagues", response_model=List[LeagueSchema])
def list_leagues(
    _user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> List[League]:
    return db.query(League).order_by(League.league_name).all()


@router.get("/teams", response_model=List[TeamSchema])
def list_teams(
    _user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
    league_id: Annotated[Optional[int], Query()] = None,
) -> List[Team]:
    q = db.query(Team).order_by(Team.team_name)
    if league_id is not None:
        q = q.filter(Team.league_id == league_id)
    return q.all()


@router.get("/roles", response_model=List[RolesSchema])
def list_roles(
    _user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_rls)],
) -> List[Roles]:
    return db.query(Roles).order_by(Roles.role_name).all()
