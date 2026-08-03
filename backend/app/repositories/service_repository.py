"""Data-access layer for services."""
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PageParams
from app.models.service import Service
from app.repositories.base import BaseRepository
from app.repositories.service_filters import ServiceFilters, apply_filters, order_by_clause
from app.schemas.service import ServiceCreate, ServiceUpdate


class ServiceRepository(BaseRepository):
    """Queries for :class:`~app.models.service.Service`."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get(self, service_id: int) -> Optional[Service]:
        """Return a service by primary key, or ``None`` if absent."""
        result = await self.db.execute(
            select(Service).where(Service.id == service_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Service]:
        """Return a service by its unique slug, or ``None``."""
        result = await self.db.execute(
            select(Service).where(Service.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        params: PageParams,
        filters: ServiceFilters,
    ) -> tuple[Sequence[Service], int]:
        """Return a page of services matching ``filters`` and the total count."""
        count_stmt = apply_filters(select(func.count(Service.id)), filters)
        list_stmt = apply_filters(select(Service), filters).order_by(
            order_by_clause(filters)
        )

        total = (await self.db.execute(count_stmt)).scalar_one()
        items = (
            (await self.db.execute(list_stmt.offset(params.offset).limit(params.page_size)))
            .scalars()
            .all()
        )
        return items, total

    async def create(self, data: ServiceCreate, slug: str, provider_id: int) -> Service:
        """Persist a new service (``slug`` resolved by the service layer)."""
        service = Service(
            category_id=data.category_id,
            provider_id=provider_id,
            title=data.title,
            slug=slug,
            description=data.description or "",
            price=data.price,
            price_unit=data.price_unit,
            duration_minutes=data.duration_minutes,
            is_active=data.is_active,
            is_featured=data.is_featured,
            images=data.images or [],
        )
        self.db.add(service)
        await self.db.flush()
        return service

    async def update(self, service: Service, data: ServiceUpdate) -> Service:
        """Apply the set fields of ``data`` onto ``service`` in place."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(service, field, value)
        await self.db.flush()
        return service

    async def delete(self, service: Service) -> None:
        """Remove a service from the database."""
        await self.db.delete(service)
        await self.db.flush()
