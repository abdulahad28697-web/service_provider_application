"""Review ORM model.

A customer's rating and comment for a completed booking. A booking may have at
most one review (enforced by a unique constraint on ``booking_id``). Reviews
feed the provider's average rating shown across the platform.
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Review(Base, TimestampMixin):
    """A customer's rating and comment for a completed booking."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("booking_id", name="uq_review_booking"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    comment: Mapped[str] = mapped_column(String(1000), default="")

    booking = relationship("Booking", foreign_keys=[booking_id])
    customer = relationship("User", foreign_keys=[customer_id])

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"<Review id={self.id} rating={self.rating} booking={self.booking_id}>"
