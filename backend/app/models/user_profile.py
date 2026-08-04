"""User profile, address, and favorite-provider ORM models."""

from typing import Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    """Optional profile information for a registered user."""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        index=True,
    )

    phone_number: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )

    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    profile_picture_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )


class UserAddress(Base, TimestampMixin):
    """A saved address belonging to a user."""

    __tablename__ = "user_addresses"

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

    label: Mapped[str] = mapped_column(
        String(50),
        default="Home",
    )

    address_line_1: Mapped[str] = mapped_column(
        String(255)
    )

    address_line_2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str] = mapped_column(
        String(100)
    )

    state_or_province: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    postal_code: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        default="Pakistan",
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )


class FavoriteProvider(Base, TimestampMixin):
    """A provider saved by a customer."""

    __tablename__ = "favorite_providers"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider_id",
            name="uq_user_favorite_provider",
        ),
    )

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

    provider_id: Mapped[int] = mapped_column(
        ForeignKey(
            "providers.id",
            ondelete="CASCADE",
        ),
        index=True,
    )