"""Password hashing and JWT creation/validation utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plain-text password for storage."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    except Exception:
        return False


def _create_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT with an explicit token purpose."""
    now = datetime.now(timezone.utc)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_access_token(
    subject: str,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed access token."""
    claims: Dict[str, Any] = {}

    if role:
        claims["role"] = role

    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=(
            expires_delta
            or timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        ),
        additional_claims=claims,
    )


def decode_access_token(
    token: str,
) -> Dict[str, Any]:
    """Decode and validate an access token."""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError(
            "Token is not an access token."
        )

    return payload


def create_password_reset_token(
    subject: str,
) -> str:
    """Create a short-lived password-reset token."""
    expiration_minutes = getattr(
        settings,
        "PASSWORD_RESET_EXPIRE_MINUTES",
        15,
    )

    return _create_token(
        subject=subject,
        token_type="password_reset",
        expires_delta=timedelta(
            minutes=expiration_minutes
        ),
    )


def decode_password_reset_token(
    token: str,
) -> Dict[str, Any]:
    """Decode and validate a password-reset token."""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    if payload.get("type") != "password_reset":
        raise jwt.InvalidTokenError(
            "Token is not a password-reset token."
        )

    return payload