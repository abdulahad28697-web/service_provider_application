"""Messaging ORM model.

Messages are linked to a booking so customers and providers can communicate
about a specific service request.
"""

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Message(Base, TimestampMixin):
    """A message exchanged between two booking participants."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    booking_id: Mapped[int] = mapped_column(
        ForeignKey(
            "bookings.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    receiver_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )

    booking = relationship(
        "Booking",
        foreign_keys=[booking_id],
    )

    sender = relationship(
        "User",
        foreign_keys=[sender_id],
    )

    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Message id={self.id} "
            f"booking={self.booking_id} "
            f"sender={self.sender_id}>"
        )