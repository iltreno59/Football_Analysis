"""Зависимости FastAPI: текущий пользователь, сессия БД с контекстом RLS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db_conn import SessionLocal
from app.core.security import decode_token

security = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user_id: int
    user_login: str
    team_id: Optional[int]
    role: str


def apply_rls_context(db: Session, user: CurrentUser) -> None:
    """Выставляет переменные сессии PostgreSQL для политик RLS (SET LOCAL)."""
    db.execute(
        text("SELECT set_config('app.user_id', :v, true)"),
        {"v": str(user.user_id)},
    )
    db.execute(
        text("SELECT set_config('app.team_id', :v, true)"),
        {"v": "" if user.team_id is None else str(user.team_id)},
    )
    db.execute(
        text("SELECT set_config('app.app_role', :v, true)"),
        {"v": (user.role or "").strip().lower()},
    )


def get_db() -> Generator[Session, None, None]:
    """Сессия без RLS (логин, health)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> CurrentUser:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(creds.credentials)
        uid = int(payload.get("sub", "0"))
        if uid <= 0:
            raise ValueError("bad sub")
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    team_raw = payload.get("team_id")
    team_id: Optional[int]
    if team_raw is None or team_raw == "":
        team_id = None
    else:
        try:
            team_id = int(team_raw)
        except (TypeError, ValueError):
            team_id = None
    return CurrentUser(
        user_id=uid,
        user_login=str(payload.get("login", "")),
        team_id=team_id,
        role=str(payload.get("role", "")),
    )


def get_db_rls(
    current: Annotated[CurrentUser, Depends(get_current_user)],
) -> Generator[Session, None, None]:
    """Сессия с контекстом RLS для текущего пользователя."""
    db = SessionLocal()
    try:
        apply_rls_context(db, current)
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def require_roles(*allowed: str):
    """Разрешает доступ только указанным значениям user.role (без учёта регистра)."""

    allowed_l = {a.strip().lower() for a in allowed}

    def _dep(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        r = (user.role or "").strip().lower()
        if r not in allowed_l:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для этой операции",
            )
        return user

    return _dep
