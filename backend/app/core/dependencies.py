"""Reusable FastAPI dependencies.

``get_current_user`` is the primary dependency: it resolves the bearer token
into a :class:`~app.models.user.User`. The role-based helpers derive from it.
"""
from typing import AsyncGenerator, Optional

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import UserRole
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

# auto_error=False lets us raise a consistent AppError (uniform error body).
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current user from the Authorization header."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing or invalid authorization header.")

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired.")
    except jwt.PyJWTError:
        raise UnauthorizedError("Invalid token.")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Token is missing a subject.")

    user = await UserRepository(db).get(int(user_id))
    if user is None or not user.is_active:
        raise UnauthorizedError("User does not exist or is inactive.")
    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Alias for the current user (enforced active in :func:`get_current_user`)."""
    return user


def require_role(*roles: UserRole):
    """Build a dependency that enforces one of the given roles.

    This is a synchronous *factory*: it returns the actual (async) dependency,
    so ``require_role(...)`` can be used directly as a ``Depends`` target.
    """

    async def _role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise UnauthorizedError("You do not have permission to perform this action.")
        return user

    return _role_checker


def get_current_admin_dep():
    return require_role(UserRole.ADMIN)
