"""Business logic for booking payments."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.utils import generate_public_id
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.provider_repository import ProviderRepository
from app.schemas.payment import (
    PaymentCheckoutResponse,
    PaymentCreate,
    PaymentRead,
    PaymentStatusUpdate,
)
from app.services.notification_service import NotificationService


class PaymentService:
    """Handle payment creation, checkout, visibility, and status rules."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

        self.payments = PaymentRepository(db)
        self.bookings = BookingRepository(db)
        self.providers = ProviderRepository(db)

        self.notifications = NotificationService(db)

    # =========================================================
    # CREATE / START PAYMENT
    # =========================================================

    async def checkout(
        self,
        *,
        customer: User,
        data: PaymentCreate,
    ) -> PaymentCheckoutResponse:
        """
        Start payment for a booking.

        Rules:
        - Only the booking customer may create the payment.
        - Only one payment record is allowed per booking.
        - Payment amount always comes from the booking total.
        """

        booking = await self.bookings.get(
            data.booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        if booking.customer_id != customer.id:
            raise ForbiddenError(
                "You are not allowed to pay for this booking."
            )

        existing = await self.payments.get_by_booking(
            booking.id
        )

        if existing is not None:
            raise ConflictError(
                "A payment already exists for this booking."
            )

        transaction_reference = generate_public_id(
            "PAY-"
        )

        # -----------------------------------------------------
        # CASH
        # -----------------------------------------------------

        if data.payment_method == PaymentMethod.CASH:
            payment_status = PaymentStatus.PENDING

            checkout_message = (
                "Cash payment selected. "
                "Payment will be collected when the service is completed."
            )

        # -----------------------------------------------------
        # JAZZCASH / EASYPAISA
        # -----------------------------------------------------

        else:
            # For now we use a simulated digital checkout.
            # Later this is where real JazzCash / Easypaisa
            # gateway integration can be connected.

            payment_status = PaymentStatus.PENDING

            method_name = (
                data.payment_method.value
                .replace("_", " ")
                .title()
            )

            checkout_message = (
                f"{method_name} checkout created. "
                "Complete the payment to continue."
            )

        payment = await self.payments.create(
            booking_id=booking.id,
            customer_id=customer.id,
            provider_id=booking.provider_id,
            amount=booking.total_price,
            payment_method=data.payment_method,
            transaction_reference=transaction_reference,
            status=payment_status,
        )

        await self.db.commit()
        await self.db.refresh(payment)

        return PaymentCheckoutResponse(
            payment_id=payment.id,
            booking_id=booking.id,
            transaction_reference=(
                payment.transaction_reference
            ),
            payment_method=payment.payment_method,
            amount=payment.amount,
            status=payment.status,
            message=checkout_message,
        )

    # =========================================================
    # GET PAYMENT BY BOOKING
    # =========================================================

    async def get_for_booking(
        self,
        *,
        booking_id: int,
        user: User,
    ) -> PaymentRead:
        """Return payment details for a visible booking."""

        booking = await self.bookings.get(
            booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        if not await self._can_view_booking(
            booking=booking,
            user=user,
        ):
            raise ForbiddenError(
                "You are not allowed to view this payment."
            )

        payment = await self.payments.get_by_booking(
            booking.id
        )

        if payment is None:
            raise NotFoundError(
                "Payment not found for this booking."
            )

        return PaymentRead.model_validate(
            payment
        )

    # =========================================================
    # CUSTOMER PAYMENT HISTORY
    # =========================================================

    async def customer_payments(
        self,
        *,
        customer: User,
    ) -> list[PaymentRead]:
        """Return payments belonging to the current customer."""

        payments = await self.payments.list_for_customer(
            customer.id
        )

        return [
            PaymentRead.model_validate(payment)
            for payment in payments
        ]

    # =========================================================
    # PROVIDER PAYMENT HISTORY
    # =========================================================

    async def provider_payments(
        self,
        *,
        provider_user: User,
    ) -> list[PaymentRead]:
        """Return payments belonging to the current provider."""

        provider = await self.providers.get_by_user_id(
            provider_user.id
        )

        if provider is None:
            raise ForbiddenError(
                "Provider profile is required."
            )

        payments = await self.payments.list_for_provider(
            provider.id
        )

        return [
            PaymentRead.model_validate(payment)
            for payment in payments
        ]

    # =========================================================
    # ADMIN PAYMENT HISTORY
    # =========================================================

    async def all_payments(
        self,
    ) -> list[PaymentRead]:
        """Return every payment for administrator use."""

        payments = await self.payments.list_all()

        return [
            PaymentRead.model_validate(payment)
            for payment in payments
        ]

    # =========================================================
    # SIMULATE DIGITAL PAYMENT SUCCESS
    # =========================================================

    async def simulate_success(
        self,
        *,
        payment_id: int,
        customer: User,
    ) -> PaymentRead:
        """
        Mark a JazzCash / Easypaisa payment as paid.

        Development/testing only until real gateway callbacks
        are integrated.
        """

        payment = await self.payments.get(
            payment_id
        )

        if payment is None:
            raise NotFoundError(
                "Payment not found."
            )

        if payment.customer_id != customer.id:
            raise ForbiddenError(
                "You are not allowed to complete this payment."
            )

        if payment.payment_method == PaymentMethod.CASH:
            raise ConflictError(
                "Cash payments cannot be completed through digital checkout."
            )

        if payment.status == PaymentStatus.PAID:
            return PaymentRead.model_validate(
                payment
            )

        if payment.status not in {
            PaymentStatus.PENDING,
            PaymentStatus.FAILED,
        }:
            raise ConflictError(
                "Payment cannot be completed from "
                f"'{payment.status.value}' status."
            )

        gateway_reference = generate_public_id(
            "GW-"
        )

        await self.payments.update_status(
            payment,
            status=PaymentStatus.PAID,
            gateway_reference=gateway_reference,
            failure_reason=None,
        )

        await self._notify_payment_paid(
            payment
        )

        await self.db.commit()
        await self.db.refresh(payment)

        return PaymentRead.model_validate(
            payment
        )

    # =========================================================
    # SIMULATE DIGITAL PAYMENT FAILURE
    # =========================================================

    async def simulate_failure(
        self,
        *,
        payment_id: int,
        customer: User,
        reason: str | None = None,
    ) -> PaymentRead:
        """Mark a digital payment as failed for testing."""

        payment = await self.payments.get(
            payment_id
        )

        if payment is None:
            raise NotFoundError(
                "Payment not found."
            )

        if payment.customer_id != customer.id:
            raise ForbiddenError(
                "You are not allowed to update this payment."
            )

        if payment.payment_method == PaymentMethod.CASH:
            raise ConflictError(
                "Cash payments do not use digital checkout."
            )

        if payment.status == PaymentStatus.PAID:
            raise ConflictError(
                "A paid payment cannot be marked failed."
            )

        if payment.status == PaymentStatus.REFUNDED:
            raise ConflictError(
                "A refunded payment cannot be marked failed."
            )

        await self.payments.update_status(
            payment,
            status=PaymentStatus.FAILED,
            failure_reason=(
                reason or
                "Payment was not completed."
            ),
        )

        await self.db.commit()
        await self.db.refresh(payment)

        return PaymentRead.model_validate(
            payment
        )

    # =========================================================
    # CASH PAYMENT COMPLETION
    # =========================================================

    async def mark_cash_paid(
        self,
        *,
        payment_id: int,
        provider_user: User,
    ) -> PaymentRead:
        """
        Provider confirms that cash was collected.

        Cash can only be marked paid after the booking has
        been completed.
        """

        payment = await self.payments.get(
            payment_id
        )

        if payment is None:
            raise NotFoundError(
                "Payment not found."
            )

        provider = await self.providers.get_by_user_id(
            provider_user.id
        )

        if provider is None:
            raise ForbiddenError(
                "Provider profile is required."
            )

        if payment.provider_id != provider.id:
            raise ForbiddenError(
                "This payment does not belong to your provider account."
            )

        if payment.payment_method != PaymentMethod.CASH:
            raise ConflictError(
                "Only cash payments can be confirmed manually."
            )

        booking = await self.bookings.get(
            payment.booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        booking_status = getattr(
            booking.status,
            "value",
            booking.status,
        )

        if booking_status != "completed":
            raise ConflictError(
                "Cash payment can only be confirmed after "
                "the booking is completed."
            )

        if payment.status == PaymentStatus.PAID:
            return PaymentRead.model_validate(
                payment
            )

        if payment.status == PaymentStatus.REFUNDED:
            raise ConflictError(
                "A refunded payment cannot be marked paid."
            )

        await self.payments.update_status(
            payment,
            status=PaymentStatus.PAID,
            failure_reason=None,
        )

        await self._notify_payment_paid(
            payment
        )

        await self.db.commit()
        await self.db.refresh(payment)

        return PaymentRead.model_validate(
            payment
        )

    # =========================================================
    # ADMIN STATUS UPDATE
    # =========================================================

    async def update_status(
        self,
        *,
        payment_id: int,
        data: PaymentStatusUpdate,
    ) -> PaymentRead:
        """Allow an administrator to update payment status."""

        payment = await self.payments.get(
            payment_id
        )

        if payment is None:
            raise NotFoundError(
                "Payment not found."
            )

        previous_status = payment.status

        await self.payments.update_status(
            payment,
            status=data.status,
            gateway_reference=data.gateway_reference,
            failure_reason=data.failure_reason,
        )

        if (
            data.status == PaymentStatus.PAID
            and previous_status != PaymentStatus.PAID
        ):
            await self._notify_payment_paid(
                payment
            )

        await self.db.commit()
        await self.db.refresh(payment)

        return PaymentRead.model_validate(
            payment
        )

    # =========================================================
    # PAYMENT PAID NOTIFICATION
    # =========================================================

    async def _notify_payment_paid(
        self,
        payment: Payment,
    ) -> None:
        """Notify both participants when a payment is confirmed."""

        provider = await self.providers.get(
            payment.provider_id
        )

        if provider is not None:
            await self.notifications.create(
                user_id=provider.user_id,
                title="Payment received",
                message=(
                    f"Payment {payment.transaction_reference} "
                    f"for booking #{payment.booking_id} "
                    "has been marked paid."
                ),
                notification_type="payment_paid",
                reference_id=payment.booking_id,
            )

        await self.notifications.create(
            user_id=payment.customer_id,
            title="Payment successful",
            message=(
                "Your payment "
                f"{payment.transaction_reference} "
                "has been confirmed."
            ),
            notification_type="payment_paid",
            reference_id=payment.booking_id,
        )

    # =========================================================
    # BOOKING VISIBILITY
    # =========================================================

    async def _can_view_booking(
        self,
        *,
        booking,
        user: User,
    ) -> bool:
        """Check whether a user may see payment data for a booking."""

        role = getattr(
            user.role,
            "value",
            user.role,
        )

        if role == "admin":
            return True

        if booking.customer_id == user.id:
            return True

        provider = await self.providers.get_by_user_id(
            user.id
        )

        return (
            provider is not None
            and provider.id == booking.provider_id
        )