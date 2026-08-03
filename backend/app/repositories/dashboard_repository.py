"""Data-access layer for the admin dashboard statistics."""
from datetime import date
from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus
from app.models.booking import Booking
from app.models.provider import Provider
from app.models.review import Review
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.dashboard import BookingSummary


class DashboardRepository(BaseRepository):
    """Aggregate statistics for the admin dashboard."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get_stats(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        """Return a dict of dashboard aggregates (optionally date-scoped)."""
        booking_where = []
        if start_date:
            booking_where.append(Booking.created_at >= start_date)
        if end_date:
            booking_where.append(Booking.created_at <= end_date)

        total_bookings = (
            await self.db.execute(select(func.count(Booking.id)).where(*booking_where))
        ).scalar_one()

        revenue_stmt = (
            select(func.coalesce(func.sum(Booking.total_price), 0))
            .where(Booking.status == BookingStatus.COMPLETED)
        )
        if booking_where:
            revenue_stmt = revenue_stmt.where(*booking_where)
        total_revenue = (await self.db.execute(revenue_stmt)).scalar_one()

        total_users = (await self.db.execute(select(func.count(User.id)))).scalar_one()
        total_providers = (
            await self.db.execute(select(func.count(Provider.id)))
        ).scalar_one()

        avg_rating = (await self.db.execute(select(func.avg(Review.rating)))).scalar_one_or_none()
        avg_rating = float(avg_rating) if avg_rating is not None else 0.0

        recent = (
            (await self.db.execute(select(Booking).order_by(Booking.created_at.desc()).limit(5)))
            .scalars()
            .all()
        )
        recent_bookings: List[BookingSummary] = [
            BookingSummary(
                id=b.id,
                customer_name=b.customer.full_name if b.customer else "Unknown",
                service_name=b.service_title,
                price=b.total_price,
                status=b.status.value,
                scheduled_date=b.scheduled_date,
            )
            for b in recent
        ]

        return {
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "total_users": total_users,
            "total_providers": total_providers,
            "average_rating": avg_rating,
            "recent_bookings": recent_bookings,
        }
