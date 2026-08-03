"""Category ORM model.

A high-level grouping that services belong to (e.g. "Cleaning", "Repair").
The ``slug`` is a URL-safe, unique key used in route paths and lookups.
"""
from typing import List

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    """A high-level grouping that services belong to (e.g. "Cleaning", "Repair")."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    services: Mapped[List["Service"]] = relationship(  # noqa: F821
        back_populates="category"
    )

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"<Category id={self.id} name={self.name!r}>"
