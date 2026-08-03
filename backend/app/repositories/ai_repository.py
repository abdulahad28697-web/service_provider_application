"""Data-access layer for AI assistant queries.

The assistant's features (chatbot, recommendations) are rule-based and query
the same provider/service tables the rest of the platform uses. This repository
wraps those lookups so the AI service layer stays thin.
"""
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import Provider
from app.models.service import Service
from app.repositories.base import BaseRepository


class AIRepository(BaseRepository):
    """Queries backing the AI assistant."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def search_providers_by_keyword(
        self, keyword: str, limit: int = 5
    ) -> Sequence[Provider]:
        """Find providers whose business name, description or category match."""
        pattern = f"%{keyword}%"
        result = await self.db.execute(
            select(Provider)
            .where(
                Provider.business_name.ilike(pattern)
                | Provider.description.ilike(pattern)
                | Provider.category.ilike(pattern)
            )
            .order_by(Provider.rating.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_providers(self, limit: int = 5) -> Sequence[Provider]:
        """Return the top-rated providers (recommendation fallback)."""
        result = await self.db.execute(
            select(Provider).order_by(Provider.rating.desc()).limit(limit)
        )
        return result.scalars().all()

    async def search_services_by_price(
        self, max_price: Decimal, limit: int = 5
    ) -> Sequence[Service]:
        """Find services priced at or below ``max_price``."""
        result = await self.db.execute(
            select(Service).where(Service.price <= max_price).limit(limit)
        )
        return result.scalars().all()
