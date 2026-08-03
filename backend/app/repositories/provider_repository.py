"""Data-access layer for providers."""
from typing import Optional

from sqlalchemy import select

from app.models.provider import Provider
from app.repositories.base import BaseRepository


class ProviderRepository(BaseRepository):
    """Queries for :class:`~app.models.provider.Provider`."""

    async def get_by_user_id(self, user_id: int) -> Optional[Provider]:
        """Return the provider profile belonging to a user, or ``None``."""
        result = await self.db.execute(
            select(Provider).where(Provider.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_owner_user_id(self, provider_id: int) -> Optional[int]:
        """Return the id of the user who owns a provider profile, if any."""
        result = await self.db.execute(
            select(Provider.user_id).where(Provider.id == provider_id)
        )
        return result.scalar_one_or_none()
