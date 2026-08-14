"""HTTP endpoints for booking payments."""

from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import (
    StandardResponse,
    success_response,
)
from app.core.dependencies import get_current_user
from app.core.permissions import (
    require_admin,
    require_customer,
    require_provider,
)
from app.database.session import get_db
from app.models.user import User
from app.schemas.payment import (
    PaymentCheckoutResponse,
    PaymentCreate,
    PaymentRead,
    PaymentStatusUpdate,
)
from app.services.payment_service import (
    PaymentService,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


# ============================================================
# LOCAL REQUEST SCHEMA
# ============================================================


class PaymentFailureRequest(BaseModel):
    """Optional reason when simulating a failed payment."""

    reason: Optional[str] = Field(
        default=None,
        max_length=500,
    )


# ============================================================
# SERVICE DEPENDENCY
# ============================================================


def _service(
    db: AsyncSession = Depends(get_db),
) -> PaymentService:
    """Build PaymentService for the current request."""

    return PaymentService(db)


# ============================================================
# CUSTOMER - START CHECKOUT
# ============================================================


@router.post(
    "/checkout",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start payment checkout",
)
async def checkout_payment(
    payload: PaymentCreate,
    service: PaymentService = Depends(_service),
    customer: User = Depends(require_customer),
):
    """
    Create a payment for one of the customer's bookings.

    Supported methods:

    - cash
    - jazzcash
    - easypaisa
    """

    checkout = await service.checkout(
        customer=customer,
        data=payload,
    )

    return success_response(
        data=PaymentCheckoutResponse.model_validate(
            checkout
        ),
        message="Payment checkout created.",
    )


# ============================================================
# CUSTOMER - PAYMENT HISTORY
#
# Keep static routes before dynamic /{payment_id}/...
# ============================================================


@router.get(
    "/me",
    response_model=StandardResponse,
    summary="List my payments",
)
async def my_payments(
    service: PaymentService = Depends(_service),
    customer: User = Depends(require_customer),
):
    payments = await service.customer_payments(
        customer=customer,
    )

    return success_response(
        data=[
            PaymentRead.model_validate(payment)
            for payment in payments
        ],
        message="Payments fetched.",
    )


# ============================================================
# PROVIDER - PAYMENT HISTORY
# ============================================================


@router.get(
    "/provider",
    response_model=StandardResponse,
    summary="List provider payments",
)
async def provider_payments(
    service: PaymentService = Depends(_service),
    provider: User = Depends(require_provider),
):
    payments = await service.provider_payments(
        provider_user=provider,
    )

    return success_response(
        data=[
            PaymentRead.model_validate(payment)
            for payment in payments
        ],
        message="Provider payments fetched.",
    )


# ============================================================
# ADMIN - ALL PAYMENTS
# ============================================================


@router.get(
    "/admin/all",
    response_model=StandardResponse,
    summary="List all platform payments",
)
async def admin_payments(
    service: PaymentService = Depends(_service),
    _admin: User = Depends(require_admin),
):
    payments = await service.all_payments()

    return success_response(
        data=[
            PaymentRead.model_validate(payment)
            for payment in payments
        ],
        message="Platform payments fetched.",
    )


# ============================================================
# GET PAYMENT FOR BOOKING
# ============================================================


@router.get(
    "/booking/{booking_id}",
    response_model=StandardResponse,
    summary="Get payment for a booking",
)
async def payment_for_booking(
    booking_id: int,
    service: PaymentService = Depends(_service),
    user: User = Depends(get_current_user),
):
    """
    Customer, booking provider or admin may view
    payment information for the booking.
    """

    payment = await service.get_for_booking(
        booking_id=booking_id,
        user=user,
    )

    return success_response(
        data=PaymentRead.model_validate(
            payment
        ),
        message="Payment fetched.",
    )


# ============================================================
# DEVELOPMENT - SIMULATE DIGITAL PAYMENT SUCCESS
# ============================================================


@router.post(
    "/{payment_id}/simulate-success",
    response_model=StandardResponse,
    summary="Simulate JazzCash/Easypaisa payment success",
)
async def simulate_payment_success(
    payment_id: int,
    service: PaymentService = Depends(_service),
    customer: User = Depends(require_customer),
):
    """
    Development-only endpoint.

    This will later be replaced by real JazzCash /
    Easypaisa gateway callbacks.
    """

    payment = await service.simulate_success(
        payment_id=payment_id,
        customer=customer,
    )

    return success_response(
        data=PaymentRead.model_validate(
            payment
        ),
        message="Payment completed successfully.",
    )


# ============================================================
# DEVELOPMENT - SIMULATE DIGITAL PAYMENT FAILURE
# ============================================================


@router.post(
    "/{payment_id}/simulate-failure",
    response_model=StandardResponse,
    summary="Simulate JazzCash/Easypaisa payment failure",
)
async def simulate_payment_failure(
    payment_id: int,
    payload: Optional[
        PaymentFailureRequest
    ] = None,
    service: PaymentService = Depends(_service),
    customer: User = Depends(require_customer),
):
    reason = (
        payload.reason
        if payload
        else None
    )

    payment = await service.simulate_failure(
        payment_id=payment_id,
        customer=customer,
        reason=reason,
    )

    return success_response(
        data=PaymentRead.model_validate(
            payment
        ),
        message="Payment marked as failed.",
    )


# ============================================================
# PROVIDER - CONFIRM CASH PAYMENT
# ============================================================


@router.post(
    "/{payment_id}/cash-paid",
    response_model=StandardResponse,
    summary="Confirm cash payment received",
)
async def confirm_cash_payment(
    payment_id: int,
    service: PaymentService = Depends(_service),
    provider: User = Depends(require_provider),
):
    """
    Provider confirms collection of a cash payment.

    Booking must already be completed.
    """

    payment = await service.mark_cash_paid(
        payment_id=payment_id,
        provider_user=provider,
    )

    return success_response(
        data=PaymentRead.model_validate(
            payment
        ),
        message="Cash payment confirmed.",
    )


# ============================================================
# ADMIN - UPDATE PAYMENT STATUS
# ============================================================


@router.patch(
    "/admin/{payment_id}/status",
    response_model=StandardResponse,
    summary="Update payment status as admin",
)
async def admin_update_payment_status(
    payment_id: int,
    payload: PaymentStatusUpdate,
    service: PaymentService = Depends(_service),
    _admin: User = Depends(require_admin),
):
    payment = await service.update_status(
        payment_id=payment_id,
        data=payload,
    )

    return success_response(
        data=PaymentRead.model_validate(
            payment
        ),
        message="Payment status updated.",
    )