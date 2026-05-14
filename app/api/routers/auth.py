"""Роут аутентификации (JWT)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.core.db_conn import SessionLocal
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _lookup_user_row(db: Session, login: str) -> dict | None:
    try:
        row = db.execute(
            text("SELECT * FROM lookup_user_for_login(:login)"),
            {"login": login},
        ).mappings().first()
        return dict(row) if row else None
    except ProgrammingError:
        u = db.query(User).filter(User.user_login == login).first()
        if not u:
            return None
        return {
            "user_id": u.user_id,
            "user_login": u.user_login,
            "hashed_password": u.hashed_password,
            "user_role": u.user_role,
            "team_id": u.team_id,
        }


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    db = SessionLocal()
    try:
        row = _lookup_user_row(db, body.user_login.strip())
        if not row or not verify_password(
            body.password, str(row["hashed_password"])
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect login or password",
            )
        token = create_access_token(
            user_id=int(row["user_id"]),
            user_login=str(row["user_login"]),
            team_id=row.get("team_id"),
            role=str(row["user_role"] or ""),
        )
        return TokenResponse(access_token=token)
    finally:
        db.close()
