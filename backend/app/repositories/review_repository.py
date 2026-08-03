"""Data-access layer for reviews."""
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.review import Review
from app.repositories.base import BaseRepository
from app.schemas.review import ReviewCreate


class ReviewRepository(BaseRepository):
    """Queries for :class:`~app.models.review.Review`."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get(self, review_id: int) -> Optional[Review]:
        """Return a review by primary key, or ``None``."""
        result = await self.db.execute(select(Review).where(Review.id == review_id))
        return result.scalar_one_or_none()

    async def get_by_booking_id(self, booking_id: int) -> Optional[Review]:
        """Return the (single) review for a booking, or ``None``."""
        result = await self.db.execute(
            select(Review).where(Review.booking_id == booking_id)
        )
        return result.scalar_one_or_none()

    async def create(self, customer_id: int, data: ReviewCreate) -> Review:
        """Persist a new review."""
        review = Review(
            booking_id=data.booking_id,
            customer_id=customer_id,
            rating=data.rating,
            comment=data.comment or "",
        )
        self.db.add(review)
        await self.db.flush()
        return review

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[Review]:
        """Return reviews, most recent first."""
        result = await self.db.execute(
            select(Review).order_by(Review.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_average_rating_for_provider(self, provider_id: int) -> float:
        """Return the average rating across a provider's bookings' reviews."""
        stmt = (
            select(func.avg(Review.rating))
            .join(Booking, Review.booking_id == Booking.id)
            .where(Booking.provider_id == provider_id)
        )
        value = (await self.db.execute(stmt)).scalar_one_or_none()
        return float(value) if value is not None else 0.0
