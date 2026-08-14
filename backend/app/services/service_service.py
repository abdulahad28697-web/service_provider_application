"""Business logic for services."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus
from app.common.pagination import Page, PageParams
from app.common.utils import slugify
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.booking import Booking
from app.models.provider import Provider
from app.models.review import Review
from app.models.service import Service
from app.models.user import User
from app.repositories.category_repository import CategoryRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.service_filters import ServiceFilters
from app.repositories.service_repository import ServiceRepository
from app.schemas.category import CategoryCreate
from app.schemas.service import (
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
)


class ServiceService:
    """Encapsulates service operations and their invariants."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ServiceRepository(db)
        self.categories = CategoryRepository(db)
        self.providers = ProviderRepository(db)

    async def get(self, service_id: int) -> Service:
        """Return a service, raising NotFoundError if missing."""

        service = await self.repo.get(service_id)

        if service is None:
            raise NotFoundError("Service not found.")

        return service

    async def get_read(
        self,
        service_id: int,
        include_inactive: bool = False,
    ) -> ServiceRead:
        """Return a hydrated ServiceRead."""

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
        """Return a page of services matching filters."""

        if (
            not include_inactive
            and filters.is_active is None
        ):
            filters.is_active = True

        items, total = await self.repo.list(
            params,
            filters,
        )

        reads = [
            await self._to_read(service)
            for service in items
        ]

        return Page.create(
            reads,
            total,
            params.page,
            params.page_size,
        )

    # =========================================================
    # CREATE
    # =========================================================

    async def create(
        self,
        data: ServiceCreate,
        provider: Provider,
    ) -> Service:
        """Create a service for the current provider."""

        category = None

        # -----------------------------------------------------
        # CATEGORY RESOLUTION
        # -----------------------------------------------------

        if data.category_id is not None:
            category = await self.categories.get(
                data.category_id
            )

        elif data.category_name:
            category_name = data.category_name.strip()

            category = await self.categories.get_by_name(
                category_name
            )

            # Category does not exist -> create it automatically
            if category is None:
                category_slug = slugify(category_name)

                # Double check slug in case different spelling/case
                existing_by_slug = (
                    await self.categories.get_by_slug(
                        category_slug
                    )
                )

                if existing_by_slug is not None:
                    category = existing_by_slug

                else:
                    category_data = CategoryCreate(
                        name=category_name,
                    )

                    category = await self.categories.create(
                        category_data,
                        category_slug,
                    )

        if category is None:
            raise NotFoundError(
                "A valid category is required."
            )

        # -----------------------------------------------------
        # UNIQUE SERVICE SLUG
        # -----------------------------------------------------

        base_slug = (
            slugify(data.slug)
            if data.slug
            else slugify(data.title)
        )

        slug = f"{base_slug}-{provider.id}"

        existing = await self.repo.get_by_slug(slug)

        if existing is not None:
            counter = 2

            while (
                await self.repo.get_by_slug(
                    f"{slug}-{counter}"
                )
                is not None
            ):
                counter += 1

            slug = f"{slug}-{counter}"

        # -----------------------------------------------------
        # CREATE SERVICE
        # -----------------------------------------------------

        service = await self.repo.create(
            data=data,
            slug=slug,
            provider_id=provider.id,
            category_id=category.id,
        )

        await self.db.commit()
        await self.db.refresh(service)

        return service

    # =========================================================
    # UPDATE
    # =========================================================

    async def update(
        self,
        service_id: int,
        data: ServiceUpdate,
        user: User,
    ) -> Service:
        """Update a service owned by the provider/admin."""

        service = await self.get(service_id)

        await self._assert_can_manage(
            service,
            user,
        )

        payload = data.model_dump(
            exclude_unset=True
        )

        # -----------------------------------------------------
        # CATEGORY NAME
        # -----------------------------------------------------

        category_name = payload.pop(
            "category_name",
            None,
        )

        if category_name:
            category_name = category_name.strip()

            category = await self.categories.get_by_name(
                category_name
            )

            if category is None:
                category_slug = slugify(category_name)

                existing_by_slug = (
                    await self.categories.get_by_slug(
                        category_slug
                    )
                )

                if existing_by_slug is not None:
                    category = existing_by_slug
                else:
                    category_data = CategoryCreate(
                        name=category_name,
                    )

                    category = await self.categories.create(
                        category_data,
                        category_slug,
                    )

            payload["category_id"] = category.id

        # -----------------------------------------------------
        # CATEGORY ID
        # -----------------------------------------------------

        elif "category_id" in payload:
            category = await self.categories.get(
                payload["category_id"]
            )

            if category is None:
                raise NotFoundError(
                    "Category not found."
                )

        # -----------------------------------------------------
        # SLUG
        # -----------------------------------------------------

        if "slug" in payload and payload["slug"]:
            base_slug = slugify(
                payload["slug"]
            )

            new_slug = (
                f"{base_slug}-{service.provider_id}"
            )

            if new_slug != service.slug:
                existing = await self.repo.get_by_slug(
                    new_slug
                )

                if (
                    existing is not None
                    and existing.id != service.id
                ):
                    counter = 2

                    candidate = (
                        f"{new_slug}-{counter}"
                    )

                    while (
                        await self.repo.get_by_slug(
                            candidate
                        )
                        is not None
                    ):
                        counter += 1

                        candidate = (
                            f"{new_slug}-{counter}"
                        )

                    new_slug = candidate

            payload["slug"] = new_slug

        updated = await self.repo.update(
            service,
            ServiceUpdate(**payload),
        )

        await self.db.commit()
        await self.db.refresh(updated)

        return updated

    # =========================================================
    # DELETE / SOFT DELETE
    # =========================================================

    async def delete(
        self,
        service_id: int,
        user: User,
    ) -> None:
        """Soft-delete a service by marking it inactive."""

        service = await self.get(service_id)

        await self._assert_can_manage(
            service,
            user,
        )

        service.is_active = False

        await self.db.commit()
        await self.db.refresh(service)

    # =========================================================
    # PERMISSIONS
    # =========================================================

    async def _assert_can_manage(
        self,
        service: Service,
        user: User,
    ) -> None:
        """Check whether user can manage this service."""

        if user.role.value == "admin":
            return

        owner_id = (
            await self.providers.get_owner_user_id(
                service.provider_id
            )
        )

        if owner_id != user.id:
            raise ForbiddenError(
                "You are not allowed to manage this service."
            )

    # =========================================================
    # READ MODEL
    # =========================================================

    async def _to_read(
        self,
        service: Service,
    ) -> ServiceRead:
        """Convert Service ORM object into a hydrated ServiceRead."""

        read = ServiceRead.model_validate(service)

        # -----------------------------------------------------
        # CATEGORY NAME
        # -----------------------------------------------------

        category = await self.categories.get(
            service.category_id
        )

        if category:
            read.category_name = category.name

        # -----------------------------------------------------
        # PROVIDER NAME + AVERAGE RATING
        # -----------------------------------------------------

        provider_result = await self.db.execute(
            select(
                User.full_name,
                Provider.rating,
            )
            .join(
                Provider,
                Provider.user_id == User.id,
            )
            .where(
                Provider.id == service.provider_id
            )
        )

        provider_row = provider_result.first()

        if provider_row is not None:
            read.provider_name = provider_row[0]
            read.provider_rating = float(
                provider_row[1] or 0
            )
        else:
            read.provider_name = None
            read.provider_rating = 0.0

        # -----------------------------------------------------
        # REVIEW COUNT FOR THIS PROVIDER
        # -----------------------------------------------------

        review_count_result = await self.db.execute(
            select(func.count(Review.id))
            .join(
                Booking,
                Review.booking_id == Booking.id,
            )
            .where(
                Booking.provider_id == service.provider_id
            )
        )

        read.review_count = int(
            review_count_result.scalar() or 0
        )

        return read