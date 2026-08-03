"""Provider ORM model.

A verified professional who offers services. This is a minimal schema so the
Service and Booking models can reference providers; the provider-verification
team is expected to expand it (verification status, documents, geo fields, etc.)
in their own scope. Do not extend it beyond what the core platform needs.
"""
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Provider(Base, TimestampMixin):
    """A verified professional who offers services."""

    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    business_name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(String(1000), default="")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"))
    city: Mapped[str] = mapped_column(String(120), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    # Category and hourly rate drive the AI search/recommendation features and
    # provider-rate comparisons. ``category`` is a free-text label such as
    # "Plumbing", "Cleaning" or "IT".
    category: Mapped[str] = mapped_column(String(120), default="", index=True)
    hourly_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return f"<Provider id={self.id} business={self.business_name}>"
