"""Service ORM model.

A concrete, priced offering a provider lists under a category.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.constants import PriceUnit
from app.database.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.category import Category
    from app.models.provider import Provider


class Service(Base, TimestampMixin):
    """A concrete, priced offering a provider lists under a category."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "categories.id",
            ondelete="RESTRICT",
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

    title: Mapped[str] = mapped_column(
        String(200),
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(220),
        unique=True,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0,
    )

    price_unit: Mapped[PriceUnit] = mapped_column(
        Enum(
            PriceUnit,
            name="price_unit",
        ),
        default=PriceUnit.PER_HOUR,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    images: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    category: Mapped[Optional["Category"]] = relationship(
        back_populates="services"
    )

    provider: Mapped[Optional["Provider"]] = relationship()

    bookings: Mapped[List["Booking"]] = relationship(
        back_populates="service"
    )

    def __repr__(self) -> str:
        return (
            f"<Service id={self.id} "
            f"title={self.title!r} "
            f"provider_id={self.provider_id}>"
        )