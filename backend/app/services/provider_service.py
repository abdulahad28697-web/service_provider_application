"""Business logic for provider profiles, availability and portfolios."""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import DAY_OF_WEEK_FROM_ISO, UserRole
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from app.models.booking import Booking
from app.models.category import Category
from app.models.provider import Provider
from app.models.review import Review
from app.models.service import Service
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.provider_repository import (
    ProviderRepository,
)
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import ProviderOnboard
from app.schemas.provider import (
    PortfolioImageCreate,
    PortfolioImageRead,
    ProviderProfileUpdate,
    ProviderPublicRead,
    ProviderPublicReviewRead,
    ProviderPublicServiceRead,
    ProviderStatisticsRead,
)
from app.schemas.schedule import ScheduleSlotRead


class ProviderService:
    """Provider application and profile-management rules."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db
        self.providers = ProviderRepository(db)
        self.users = UserRepository(db)
        self.schedules = ScheduleRepository(db)
        self.bookings = BookingRepository(db)

    # ========================================================
    # APPLY TO BECOME PROVIDER
    # ========================================================

    async def apply(
        self,
        user: User,
        data: ProviderOnboard,
    ) -> Provider:
        """Create a pending provider application."""

        if user.role == UserRole.ADMIN:
            raise BadRequestError(
                "Administrators cannot apply as providers."
            )

        if await self.providers.get_by_user_id(
            user.id
        ):
            raise ConflictError(
                "A provider profile already exists for this user."
            )

        provider = await self.providers.create(
            user.id,
            data,
        )

        await self.db.commit()
        await self.db.refresh(provider)

        return provider

    # ========================================================
    # LEGACY PROVIDER ONBOARDING
    # ========================================================

    async def onboard(
        self,
        user: User,
        data: ProviderOnboard,
    ) -> Provider:
        """Legacy onboarding for an existing provider-role user."""

        if user.role != UserRole.PROVIDER:
            raise NotFoundError(
                "Only provider accounts can create a provider profile."
            )

        if await self.providers.get_by_user_id(
            user.id
        ):
            raise ConflictError(
                "A provider profile already exists for this user."
            )

        provider = await self.providers.create(
            user.id,
            data,
        )

        await self.db.commit()
        await self.db.refresh(provider)

        return provider

    # ========================================================
    # MY PROVIDER PROFILE
    # ========================================================

    async def get_my_profile(
        self,
        user: User,
    ) -> Provider:
        """Return the current provider's profile."""

        provider = await self.providers.get_by_user_id(
            user.id
        )

        if provider is None:
            raise NotFoundError(
                "Provider profile not found."
            )

        return provider

    # ========================================================
    # UPDATE MY PROFILE
    # ========================================================

    async def update_my_profile(
        self,
        user: User,
        data: ProviderProfileUpdate,
    ) -> Provider:
        """Update the current provider's profile."""

        if not data.model_fields_set:
            raise BadRequestError(
                "At least one provider field is required."
            )

        provider = await self.get_my_profile(
            user
        )

        provider = await self.providers.update_profile(
            provider,
            data,
        )

        await self.db.commit()
        await self.db.refresh(provider)

        return provider

    # ========================================================
    # MY PORTFOLIO
    # ========================================================

    async def list_portfolio(
        self,
        user: User,
    ):
        """Return current provider portfolio."""

        provider = await self.get_my_profile(
            user
        )

        return await self.providers.list_portfolio_images(
            provider.id
        )

    # ========================================================
    # ADD PORTFOLIO IMAGE
    # ========================================================

    async def add_portfolio_image(
        self,
        user: User,
        data: PortfolioImageCreate,
    ):
        """Add a portfolio image."""

        provider = await self.get_my_profile(
            user
        )

        image = await self.providers.add_portfolio_image(
            provider.id,
            data,
        )

        await self.db.commit()
        await self.db.refresh(image)

        return image

    # ========================================================
    # DELETE PORTFOLIO IMAGE
    # ========================================================

    async def delete_portfolio_image(
        self,
        user: User,
        image_id: int,
    ) -> None:
        """Delete a provider portfolio image."""

        provider = await self.get_my_profile(
            user
        )

        image = await self.providers.get_portfolio_image(
            provider.id,
            image_id,
        )

        if image is None:
            raise NotFoundError(
                "Portfolio image not found."
            )

        await self.providers.delete_portfolio_image(
            image
        )

        await self.db.commit()

    # ========================================================
    # STATISTICS
    # ========================================================

    async def statistics(
        self,
        user: User,
    ) -> ProviderStatisticsRead:
        """Return provider dashboard statistics."""

        provider = await self.get_my_profile(
            user
        )

        values = await self.providers.statistics(
            provider.id
        )

        return ProviderStatisticsRead(
            provider_id=provider.id,
            average_rating=provider.rating,
            **values,
        )

    # ========================================================
    # PUBLIC PROVIDER AVAILABILITY
    # ========================================================

    async def public_availability(
        self,
        provider_id: int,
    ) -> list[ScheduleSlotRead]:
        """Return public weekly availability for a verified provider."""

        provider = await self.providers.get(
            provider_id
        )

        if provider is None or not provider.is_verified:
            raise NotFoundError(
                "Provider not found."
            )

        rows = await self.schedules.list(
            provider.id
        )

        return [
            ScheduleSlotRead.model_validate(row)
            for row in rows
            if row.is_available
        ]

    # ========================================================
    # PUBLIC AVAILABLE BOOKING SLOTS
    # ========================================================

    async def available_slots(
        self,
        provider_id: int,
        service_id: int,
        selected_date: date,
    ) -> list[str]:
        """
        Return conflict-free start times for a provider/service/date.

        Slots are generated every 30 minutes inside the provider's saved
        weekly availability. Pending and accepted bookings are excluded.
        """

        provider = await self.providers.get(
            provider_id
        )

        if provider is None or not provider.is_verified:
            raise NotFoundError(
                "Provider not found."
            )

        service_result = await self.db.execute(
            select(Service).where(
                Service.id == service_id,
                Service.provider_id == provider.id,
                Service.is_active.is_(True),
            )
        )

        service = service_result.scalar_one_or_none()

        if service is None:
            raise NotFoundError(
                "Service not found for this provider."
            )

        weekday = DAY_OF_WEEK_FROM_ISO[
            selected_date.weekday()
        ]

        schedule = await self.schedules.get_for_day(
            provider.id,
            weekday,
        )

        if (
            schedule is None
            or not schedule.is_available
        ):
            return []

        duration_minutes = max(
            int(service.duration_minutes or 60),
            1,
        )

        availability_start = datetime.combine(
            selected_date,
            schedule.start_time,
        )

        availability_end = datetime.combine(
            selected_date,
            schedule.end_time,
        )

        slots: list[str] = []
        current = availability_start

        while (
            current
            + timedelta(minutes=duration_minutes)
            <= availability_end
        ):
            slot_start = current.time()

            slot_end = (
                current
                + timedelta(minutes=duration_minutes)
            ).time()

            conflicts = await self.bookings.count_overlaps(
                provider_id=provider.id,
                scheduled_date=selected_date,
                scheduled_start=slot_start,
                scheduled_end=slot_end,
            )

            if conflicts == 0:
                slots.append(
                    slot_start.strftime("%H:%M")
                )

            current += timedelta(minutes=30)

        return slots

    # ========================================================
    # PUBLIC PROVIDER PROFILE
    # ========================================================

    async def get_public_profile(
        self,
        provider_id: int,
    ) -> ProviderPublicRead:
        """
        Return a provider profile that customers may view.

        Includes:
        - provider/business details
        - average rating
        - review count
        - portfolio
        - active services
        - customer reviews
        """

        # ----------------------------------------------------
        # PROVIDER
        # ----------------------------------------------------

        provider = await self.providers.get(
            provider_id
        )

        if provider is None:
            raise NotFoundError(
                "Provider not found."
            )

        # Only verified providers should be publicly visible.
        if not provider.is_verified:
            raise NotFoundError(
                "Provider not found."
            )

        # ----------------------------------------------------
        # PROVIDER OWNER / DISPLAY NAME
        # ----------------------------------------------------

        owner = await self.users.get(
            provider.user_id
        )

        if owner is None:
            raise NotFoundError(
                "Provider owner not found."
            )

        # ----------------------------------------------------
        # PORTFOLIO
        # ----------------------------------------------------

        portfolio_rows = (
            await self.providers.list_portfolio_images(
                provider.id
            )
        )

        portfolio = [
            PortfolioImageRead.model_validate(
                image
            )
            for image in portfolio_rows
        ]

        # ----------------------------------------------------
        # ACTIVE SERVICES
        # ----------------------------------------------------

        service_result = await self.db.execute(
            select(
                Service,
                Category.name,
            )
            .join(
                Category,
                Category.id == Service.category_id,
            )
            .where(
                Service.provider_id == provider.id,
                Service.is_active.is_(True),
            )
            .order_by(
                Service.created_at.desc()
            )
        )

        services = []

        for service_row, category_name in service_result.all():

            service_read = (
                ProviderPublicServiceRead
                .model_validate(
                    service_row
                )
            )

            service_read.category_name = (
                category_name
            )

            services.append(
                service_read
            )

        # ----------------------------------------------------
        # REVIEWS
        # ----------------------------------------------------

        review_result = await self.db.execute(
            select(
                Review,
                User.full_name,
            )
            .join(
                Booking,
                Review.booking_id == Booking.id,
            )
            .join(
                User,
                Review.customer_id == User.id,
            )
            .where(
                Booking.provider_id == provider.id
            )
            .order_by(
                Review.created_at.desc()
            )
        )

        reviews = []

        for review, customer_name in review_result.all():

            reviews.append(
                ProviderPublicReviewRead(
                    id=review.id,
                    booking_id=review.booking_id,
                    customer_id=review.customer_id,
                    customer_name=customer_name,
                    rating=review.rating,
                    comment=review.comment,
                    created_at=review.created_at,
                )
            )

        # ----------------------------------------------------
        # COMPLETE PUBLIC RESPONSE
        # ----------------------------------------------------

        return ProviderPublicRead(
            id=provider.id,
            user_id=provider.user_id,
            provider_name=owner.full_name,
            business_name=provider.business_name,
            description=provider.description or "",
            category=provider.category,
            hourly_rate=provider.hourly_rate,
            city=provider.city or "",
            address=provider.address or "",
            is_verified=provider.is_verified,
            average_rating=provider.rating,
            review_count=len(reviews),
            portfolio=portfolio,
            services=services,
            reviews=reviews,
        )