"""Data-access layer for AI assistant queries."""

from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.provider import Provider
from app.models.service import Service
from app.repositories.base import BaseRepository


class AIRepository(BaseRepository):
    """Database queries used by the AI assistant."""

    async def search_providers_by_keyword(
        self,
        keyword: str,
        limit: int = 5,
    ) -> Sequence[Provider]:
        """Find verified providers matching a keyword."""
        pattern = f"%{keyword.strip()}%"

        result = await self.db.execute(
            select(Provider)
            .where(
                Provider.is_verified.is_(True),
                (
                    Provider.business_name.ilike(pattern)
                    | Provider.description.ilike(pattern)
                    | Provider.category.ilike(pattern)
                ),
            )
            .order_by(Provider.rating.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_providers(
        self,
        limit: int = 5,
        category: Optional[str] = None,
    ) -> Sequence[Provider]:
        """Return top-rated verified providers."""
        statement = select(Provider).where(
            Provider.is_verified.is_(True)
        )

        if category:
            statement = statement.where(
                Provider.category.ilike(f"%{category.strip()}%")
            )

        result = await self.db.execute(
            statement
            .order_by(Provider.rating.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def search_services(
        self,
        *,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        limit: int = 5,
    ) -> Sequence[Service]:
        """Search active services using natural-language criteria."""
        statement = select(Service).where(
            Service.is_active.is_(True)
        )

        if query:
            pattern = f"%{query.strip()}%"
            statement = statement.where(
                Service.title.ilike(pattern)
                | Service.description.ilike(pattern)
            )

        if category:
            statement = statement.join(
                Provider,
                Provider.id == Service.provider_id,
            ).where(
                Provider.category.ilike(f"%{category.strip()}%")
            )

        if max_price is not None:
            statement = statement.where(
                Service.price <= max_price
            )

        result = await self.db.execute(
            statement
            .order_by(
                Service.is_featured.desc(),
                Service.price.asc(),
            )
            .limit(limit)
        )
        return result.scalars().all()

    async def search_services_by_price(
        self,
        max_price: Decimal,
        limit: int = 5,
    ) -> Sequence[Service]:
        """Find active services within a maximum price."""
        return await self.search_services(
            max_price=max_price,
            limit=limit,
        )

    async def get_services_by_ids(
        self,
        service_ids: Sequence[int],
    ) -> Sequence[Service]:
        """Return active services matching a collection of IDs."""
        result = await self.db.execute(
            select(Service).where(
                Service.id.in_(service_ids),
                Service.is_active.is_(True),
            )
        )
        return result.scalars().all()

    async def preferred_categories(
        self,
        customer_id: int,
        limit: int = 3,
    ) -> list[str]:
        """Find categories most frequently booked by a customer."""
        result = await self.db.execute(
            select(
                Provider.category,
                func.count(Booking.id).label("booking_count"),
            )
            .join(
                Booking,
                Booking.provider_id == Provider.id,
            )
            .where(Booking.customer_id == customer_id)
            .group_by(Provider.category)
            .order_by(func.count(Booking.id).desc())
            .limit(limit)
        )

        return [
            category
            for category, _count in result.all()
            if category
        ]