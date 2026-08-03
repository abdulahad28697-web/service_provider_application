"""Security primitives: password hashing and JWT creation/decoding.

These helpers are shared by the auth team's login/registration endpoints and by
:mod:`app.core.dependencies` (used by every protected route in this project).
Keeping them here lets each module depend on a single, consistent contract.

Uses ``bcrypt`` directly (passlib is not compatible with bcrypt>=4.x).
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.core.config import settings


# --------------------------------------------------------------------------- #
# Passwords
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    """Hash a plain-text password for storage."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# JWT access tokens
# --------------------------------------------------------------------------- #
def create_access_token(
    subject: str,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT for a user.

    Parameters
    ----------
    subject:
        Stable identifier (user id) that the token represents.
    role:
        Optional user role embedded in the token claims.
    expires_delta:
        Override for the default token lifetime (see settings).
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if role:
        payload["role"] = role
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT.

    Raises ``jwt.PyJWTError`` subclasses on invalid/expired tokens so callers
    can translate them into a 401 response.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
