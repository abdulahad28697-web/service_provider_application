"""Data-access layer for bookings."""
from datetime import date, time
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus
from app.common.pagination import PageParams
from app.models.booking import Booking
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository):
    """Queries for :class:`~app.models.booking.Booking`."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get(self, booking_id: int) -> Optional[Booking]:
        """Return a booking by primary key, or ``None`` if absent."""
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_by_reference(self, ref: str) -> Optional[Booking]:
        """Return a booking by its reference code, or ``None``."""
        result = await self.db.execute(
            select(Booking).where(Booking.reference_code == ref)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        reference_code: str,
        service_id: int,
        customer_id: int,
        provider_id: int,
        service_title: str,
        scheduled_date: date,
        scheduled_start: time,
        scheduled_end: time,
        total_price: Decimal,
        customer_notes: str = "",
        location: str = "",
    ) -> Booking:
        """Persist a new booking in the ``PENDING`` state."""
        booking = Booking(
            reference_code=reference_code,
            service_id=service_id,
            customer_id=customer_id,
            provider_id=provider_id,
            service_title=service_title,
            scheduled_date=scheduled_date,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            total_price=total_price,
            customer_notes=customer_notes,
            location=location,
            status=BookingStatus.PENDING,
        )
        self.db.add(booking)
        await self.db.flush()
        return booking

    async def count_overlaps(
        self,
        *,
        provider_id: int,
        scheduled_date: date,
        scheduled_start: time,
        scheduled_end: time,
        exclude_booking_id: Optional[int] = None,
    ) -> int:
        """Count non-terminal bookings overlapping the given time window.

        Two bookings overlap when each starts before the other ends. Only
        PENDING / ACCEPTED bookings are considered (terminal bookings free the
        slot). ``exclude_booking_id`` lets the provider accept their own booking
        without it counting as a self-conflict.
        """
        stmt = select(func.count(Booking.id)).where(
            Booking.provider_id == provider_id,
            Booking.scheduled_date == scheduled_date,
            Booking.scheduled_start < scheduled_end,
            Booking.scheduled_end > scheduled_start,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.ACCEPTED]),
        )
        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)
        return (await self.db.execute(stmt)).scalar_one()

    async def list(
        self,
        params: PageParams,
        *,
        customer_id: Optional[int] = None,
        provider_id: Optional[int] = None,
        status: Optional[BookingStatus] = None,
    ) -> tuple[Sequence[Booking], int]:
        """Return a page of bookings filtered by customer/provider/status."""
        conditions = []
        if customer_id is not None:
            conditions.append(Booking.customer_id == customer_id)
        if provider_id is not None:
            conditions.append(Booking.provider_id == provider_id)
        if status is not None:
            conditions.append(Booking.status == status)

        count_stmt = select(func.count(Booking.id))
        list_stmt = select(Booking).order_by(Booking.created_at.desc())
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            list_stmt = list_stmt.where(*conditions)

        total = (await self.db.execute(count_stmt)).scalar_one()
        items = (
            (await self.db.execute(list_stmt.offset(params.offset).limit(params.page_size)))
            .scalars()
            .all()
        )
        return items, total

    async def save(self, booking: Booking) -> Booking:
        """Flush pending changes to a booking to the database."""
        await self.db.flush()
        return booking
