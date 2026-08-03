"""Data-access layer for providers."""
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import Provider
from app.repositories.base import BaseRepository
from app.schemas.admin import ProviderOnboard


class ProviderRepository(BaseRepository):
    """Queries for :class:`~app.models.provider.Provider`."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get(self, provider_id: int) -> Optional[Provider]:
        """Return a provider profile by primary key, or ``None``."""
        result = await self.db.execute(
            select(Provider).where(Provider.id == provider_id)
        )
        return result.scalar_one_or_none()

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

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
    ) -> Sequence[Provider]:
        """Return a page of providers, optionally filtered by category."""
        stmt = select(Provider).order_by(Provider.rating.desc())
        if category:
            stmt = stmt.where(Provider.category.ilike(f"%{category}%"))
        result = await self.db.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, user_id: int, data: ProviderOnboard) -> Provider:
        """Persist a new provider profile for a user."""
        provider = Provider(
            user_id=user_id,
            business_name=data.business_name,
            description=data.description or "",
            category=data.category,
            hourly_rate=data.hourly_rate,
            city=data.city or "",
            address=data.address or "",
        )
        self.db.add(provider)
        await self.db.flush()
        return provider

    async def update_verification(self, provider: Provider, is_verified: bool) -> Provider:
        """Toggle a provider's verification status in place."""
        provider.is_verified = is_verified
        await self.db.flush()
        return provider

    async def update_rating(self, provider: Provider, new_rating) -> Provider:
        """Set a provider's average rating in place."""
        provider.rating = new_rating
        await self.db.flush()
        return provider

    async def search(
        self,
        *,
        query: Optional[str] = None,
        category: Optional[str] = None,
        min_rate: Optional[float] = None,
        max_rate: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> Sequence[Provider]:
        """Search providers by keyword, category and/or hourly-rate range."""
        stmt = select(Provider)
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                Provider.business_name.ilike(pattern)
                | Provider.description.ilike(pattern)
                | Provider.category.ilike(pattern)
            )
        if category:
            stmt = stmt.where(Provider.category.ilike(f"%{category}%"))
        if min_rate is not None:
            stmt = stmt.where(Provider.hourly_rate >= min_rate)
        if max_rate is not None:
            stmt = stmt.where(Provider.hourly_rate <= max_rate)
        stmt = stmt.order_by(Provider.rating.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
