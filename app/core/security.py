"""JWT и проверка пароля (bcrypt, как при создании пользователя)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        import bcrypt
    except ImportError as e:
        raise RuntimeError("Установите bcrypt: pip install bcrypt") from e
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    *,
    user_id: int,
    user_login: str,
    team_id: Optional[int],
    role: Optional[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "login": user_login,
        "team_id": team_id,
        "role": role or "",
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
