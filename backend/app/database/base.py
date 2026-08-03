"""Declarative base and reusable model mixins.

Every ORM model in the project derives from :class:`Base` so that
``Base.metadata.create_all()`` (used at startup) and Alembic both see the full
schema. ``TimestampMixin`` provides the audit columns used across all modules.
"""
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Single declarative base for all ORM models."""


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` audit columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
