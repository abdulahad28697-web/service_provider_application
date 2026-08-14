"""Payment ORM model."""

from enum import Enum

from sqlalchemy import (
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base, TimestampMixin


class PaymentStatus(str, Enum):
    """Supported payment lifecycle states."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Supported payment methods."""

    CASH = "cash"
    JAZZCASH = "jazzcash"
    EASYPAISA = "easypaisa"


class Payment(Base, TimestampMixin):
    """Payment record linked to a booking."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    booking_id: Mapped[int] = mapped_column(
        ForeignKey(
            "bookings.id",
            ondelete="CASCADE",
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    provider_id: Mapped[int] = mapped_column(
        ForeignKey(
            "providers.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=False,
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        SqlEnum(
            PaymentMethod,
            name="payment_method",
            native_enum=False,
        ),
        nullable=False,
    )

    status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(
            PaymentStatus,
            name="payment_status",
            native_enum=False,
        ),
        default=PaymentStatus.PENDING,
        index=True,
        nullable=False,
    )

    transaction_reference: Mapped[str | None] = mapped_column(
        String(120),
        unique=True,
        index=True,
        nullable=True,
    )

    gateway_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    booking = relationship(
        "Booking",
        foreign_keys=[booking_id],
    )

    customer = relationship(
        "User",
        foreign_keys=[customer_id],
    )

    provider = relationship(
        "Provider",
        foreign_keys=[provider_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} "
            f"booking={self.booking_id} "
            f"status={self.status.value}>"
        )