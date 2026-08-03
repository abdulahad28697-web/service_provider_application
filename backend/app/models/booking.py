"""Booking ORM model.

A customer's reservation of a service at a specific time slot. Booking rows
snapshot the service title and total price so history stays meaningful even if
the underlying service later changes. The provider *profile* id is stored so
scheduling / conflict checks share a single key with :class:`ProviderSchedule`
and :class:`Service`.
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.constants import BookingStatus
from app.database.base import Base, TimestampMixin


class Booking(Base, TimestampMixin):
    """A customer's reservation of a service at a specific time slot."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="RESTRICT"), index=True
    )

    scheduled_date: Mapped[date] = mapped_column(Date, index=True)
    scheduled_start: Mapped[time] = mapped_column(Time)
    scheduled_end: Mapped[time] = mapped_column(Time)

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        index=True,
    )
    customer_notes: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[str] = mapped_column(String(255), default="")

    # Snapshot fields so history stays meaningful even if the service changes.
    service_title: Mapped[str] = mapped_column(String(200))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    cancelled_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reject_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    service = relationship("Service", back_populates="bookings")
    customer = relationship("User", foreign_keys=[customer_id])
    provider = relationship("Provider", foreign_keys=[provider_id])

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"<Booking id={self.id} status={self.status.value}>"
