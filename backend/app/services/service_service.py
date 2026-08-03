"""Business logic for services."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus
from app.common.pagination import Page, PageParams
from app.common.utils import slugify
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.booking import Booking
from app.models.provider import Provider
from app.models.service import Service
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.service_filters import ServiceFilters
from app.repositories.service_repository import ServiceRepository
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate


class ServiceService:
    """Encapsulates service operations and their invariants."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ServiceRepository(db)
        self.categories = CategoryRepository(db)
        self.providers = ProviderRepository(db)

    async def get(self, service_id: int) -> Service:
        """Return a service, raising ``NotFoundError`` if it is missing."""
        service = await self.repo.get(service_id)
        if service is None:
            raise NotFoundError("Service not found.")
        return service

    async def get_read(
        self, service_id: int, include_inactive: bool = False
    ) -> ServiceRead:
        """Return a hydrated :class:`ServiceRead` (with category/provider names)."""
        service = await self.get(service_id)
        if not service.is_active and not include_inactive:
            raise NotFoundError("Service not found.")
        return await self._to_read(service)

    async def list(
        self,
        params: PageParams,
        filters: ServiceFilters,
        include_inactive: bool = False,
    ) -> Page[ServiceRead]:
        """Return a page of services matching ``filters``.

        By default only active services are returned; hiding inactive ones is
        the public-facing behaviour unless ``include_inactive`` is requested.
        """
        if not include_inactive and filters.is_active is None:
            filters.is_active = True

        items, total = await self.repo.list(params, filters)
        reads = [await self._to_read(s) for s in items]
        return Page.create(reads, total, params.page, params.page_size)

    async def create(self, data: ServiceCreate, provider: Provider) -> Service:
        """Create a service under a provider, validating category + slug."""
        category = await self.categories.get(data.category_id)
        if category is None:
            raise NotFoundError("Category not found.")

        slug = data.slug or slugify(data.title)
        if await self.repo.get_by_slug(slug):
            raise ConflictError("A service with this slug already exists.")

        service = await self.repo.create(data, slug, provider.id)
        await self.db.commit()
        await self.db.refresh(service)
        return service

    async def update(self, service_id: int, data: ServiceUpdate, user: User) -> Service:
        """Update a service owned by ``user`` (admins may update any)."""
        service = await self.get(service_id)
        await self._assert_can_manage(service, user)

        payload = data.model_dump(exclude_unset=True)

        if "category_id" in payload:
            category = await self.categories.get(payload["category_id"])
            if category is None:
                raise NotFoundError("Category not found.")

        new_slug = payload.get("slug") or (
            slugify(payload["title"]) if payload.get("title") else None
        )
        if new_slug and new_slug != service.slug and await self.repo.get_by_slug(new_slug):
            raise ConflictError("A service with this slug already exists.")
        if new_slug:
            payload["slug"] = new_slug

        updated = await self.repo.update(service, ServiceUpdate(**payload))
        await self.db.commit()
        await self.db.refresh(updated)
        return updated

    async def delete(self, service_id: int, user: User) -> None:
        """Delete a service, blocking the action if it has open bookings."""
        service = await self.get(service_id)
        await self._assert_can_manage(service, user)

        # Count non-terminal bookings so a service with upcoming work cannot be
        # removed out from under customers.
        from sqlalchemy import func

        open_count = (
            await self.db.execute(
                select(func.count(Booking.id)).where(
                    Booking.service_id == service_id,
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.ACCEPTED]),
                )
            )
        ).scalar_one()
        if open_count:
            raise ConflictError(
                "Cannot delete a service with pending or accepted bookings."
            )

        await self.repo.delete(service)
        await self.db.commit()

    # -- helpers -------------------------------------------------------------
    async def _assert_can_manage(self, service: Service, user: User) -> None:
        """A user may only manage their own services (admins may manage any)."""
        if user.role.value == "admin":
            return
        owner_id = await self.providers.get_owner_user_id(service.provider_id)
        if owner_id != user.id:
            raise ForbiddenError("You are not allowed to manage this service.")

    async def _to_read(self, service: Service) -> ServiceRead:
        """Hydrate a :class:`ServiceRead` with category and provider names."""
        read = ServiceRead.model_validate(service)
        category = await self.categories.get(service.category_id)
        if category:
            read.category_name = category.name

        result = await self.db.execute(
            select(User.full_name)
            .join(Provider, Provider.user_id == User.id)
            .where(Provider.id == service.provider_id)
        )
        read.provider_name = result.scalar_one_or_none()
        return read
