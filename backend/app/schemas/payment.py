"""Payment Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.payment import (
    PaymentMethod,
    PaymentStatus,
)


# ============================================================
# CREATE / CHECKOUT PAYMENT
# ============================================================


class PaymentCreate(BaseModel):
    """Payload for creating a payment for a booking."""

    booking_id: int = Field(
        ...,
        gt=0,
    )

    payment_method: PaymentMethod


# ============================================================
# PAYMENT STATUS UPDATE
# ============================================================


class PaymentStatusUpdate(BaseModel):
    """Payload for updating payment status internally/admin-side."""

    status: PaymentStatus

    gateway_reference: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    failure_reason: Optional[str] = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# PAYMENT RESPONSE
# ============================================================


class PaymentRead(BaseModel):
    """Payment information returned by the API."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    booking_id: int

    customer_id: int

    provider_id: int

    amount: Decimal

    payment_method: PaymentMethod

    status: PaymentStatus

    transaction_reference: Optional[str]

    gateway_reference: Optional[str]

    failure_reason: Optional[str]

    created_at: datetime


# ============================================================
# CHECKOUT RESPONSE
# ============================================================


class PaymentCheckoutResponse(BaseModel):
    """Returned after starting a payment."""

    payment_id: int

    booking_id: int

    transaction_reference: str

    payment_method: PaymentMethod

    amount: Decimal

    status: PaymentStatus

    message: str