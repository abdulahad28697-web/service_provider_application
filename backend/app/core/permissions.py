"""Role guards and ownership checks.

Role guards are thin wrappers over :func:`app.core.dependencies.require_role`.
Ownership helpers below are used by service-layer code to verify that the
acting user actually owns (or is the provider of) the resource.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import UserRole
from app.core.dependencies import require_role
from app.core.exceptions import ForbiddenError
from app.models.provider import Provider
from app.models.user import User
from app.repositories.provider_repository import ProviderRepository


# Convenient, prebuilt guards used in route decorators.
require_customer = require_role(UserRole.CUSTOMER, UserRole.ADMIN)
require_provider = require_role(UserRole.PROVIDER, UserRole.ADMIN)
require_admin = require_role(UserRole.ADMIN)


async def get_provider_profile(db: AsyncSession, user: User) -> Provider:
    """Resolve the provider record for a user, raising if they are not one.

    Used by routes where the acting user must have an active provider profile.
    """
    provider = await ProviderRepository(db).get_by_user_id(user.id)
    if provider is None:
        raise ForbiddenError("A provider profile is required for this action.")
    return provider


def ensure_owner(resource_owner_id: int, user: User, action: str = "perform this action") -> None:
    """Raise unless ``user.id`` matches the resource owner id."""
    if resource_owner_id != user.id:
        raise ForbiddenError(f"You are not allowed to {action} on this resource.")
