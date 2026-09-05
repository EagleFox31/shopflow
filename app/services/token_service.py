from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(
        str(user_id),
        "access",
        timedelta(minutes=settings.access_token_minutes),
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        str(user_id),
        "refresh",
        timedelta(days=settings.refresh_token_days),
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    if payload.get("type") != expected_type or not payload.get("sub"):
        raise UnauthorizedError("Invalid token type")
    return payload
