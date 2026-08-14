"""Notification ORM model."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    """A notification delivered to a user."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200)
    )

    message: Mapped[str] = mapped_column(
        Text
    )

    notification_type: Mapped[str] = mapped_column(
        String(50),
        default="general",
        index=True,
    )

    reference_id: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
    )