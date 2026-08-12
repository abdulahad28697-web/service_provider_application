"""Business logic for reviews."""

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.review import Review
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate


class ReviewService:
    """Encapsulates review operations and their invariants."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.reviews = ReviewRepository(db)
        self.bookings = BookingRepository(db)
        self.providers = ProviderRepository(db)

    async def create(
        self,
        customer: User,
        data: ReviewCreate,
    ) -> Review:
        """
        Create a review for a completed booking and update
        the provider's average rating.
        """

        # -----------------------------------------------------
        # ONLY ONE REVIEW PER BOOKING
        # -----------------------------------------------------

        existing_review = (
            await self.reviews.get_by_booking_id(
                data.booking_id
            )
        )

        if existing_review is not None:
            raise ConflictError(
                "A review already exists for this booking."
            )

        # -----------------------------------------------------
        # BOOKING MUST EXIST
        # -----------------------------------------------------

        booking = await self.bookings.get(
            data.booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        # -----------------------------------------------------
        # CUSTOMER MUST OWN THE BOOKING
        # -----------------------------------------------------

        if booking.customer_id != customer.id:
            # Do not expose another customer's booking.
            raise NotFoundError(
                "Booking not found."
            )

        # -----------------------------------------------------
        # BOOKING MUST BE COMPLETED
        # -----------------------------------------------------

        if booking.status != BookingStatus.COMPLETED:
            raise ConflictError(
                "You can only review a completed booking."
            )

        # -----------------------------------------------------
        # CREATE REVIEW
        # -----------------------------------------------------

        review = await self.reviews.create(
            customer.id,
            data,
        )

        # -----------------------------------------------------
        # UPDATE PROVIDER AVERAGE RATING
        # -----------------------------------------------------

        provider = await self.providers.get(
            booking.provider_id
        )

        if provider is not None:
            average_rating = (
                await self.reviews
                .get_average_rating_for_provider(
                    provider.id
                )
            )

            await self.providers.update_rating(
                provider,
                average_rating,
            )

        await self.db.commit()
        await self.db.refresh(review)

        return review

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Review]:
        """Return reviews, most recent first."""

        return await self.reviews.list(
            skip=skip,
            limit=limit,
        )