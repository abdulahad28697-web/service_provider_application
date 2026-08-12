"""Data-access layer for payments."""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository):
    """Queries for payment records."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        super().__init__(db)


    # =========================================================
    # GET BY ID
    # =========================================================

    async def get(
        self,
        payment_id: int,
    ) -> Optional[Payment]:
        """Return a payment by primary key."""

        result = await self.db.execute(
            select(Payment).where(
                Payment.id == payment_id
            )
        )

        return result.scalar_one_or_none()


    # =========================================================
    # GET BY BOOKING
    # =========================================================

    async def get_by_booking(
        self,
        booking_id: int,
    ) -> Optional[Payment]:
        """Return the payment associated with a booking."""

        result = await self.db.execute(
            select(Payment).where(
                Payment.booking_id == booking_id
            )
        )

        return result.scalar_one_or_none()


    # =========================================================
    # GET BY TRANSACTION REFERENCE
    # =========================================================

    async def get_by_transaction_reference(
        self,
        transaction_reference: str,
    ) -> Optional[Payment]:
        """Return a payment by public transaction reference."""

        result = await self.db.execute(
            select(Payment).where(
                Payment.transaction_reference ==
                transaction_reference
            )
        )

        return result.scalar_one_or_none()


    # =========================================================
    # CREATE
    # =========================================================

    async def create(
        self,
        *,
        booking_id: int,
        customer_id: int,
        provider_id: int,
        amount,
        payment_method: PaymentMethod,
        transaction_reference: str,
        status: PaymentStatus = PaymentStatus.PENDING,
    ) -> Payment:
        """Create a new payment record."""

        payment = Payment(
            booking_id=booking_id,
            customer_id=customer_id,
            provider_id=provider_id,
            amount=amount,
            payment_method=payment_method,
            transaction_reference=transaction_reference,
            status=status,
        )

        self.db.add(payment)

        await self.db.flush()

        return payment


    # =========================================================
    # LIST CUSTOMER PAYMENTS
    # =========================================================

    async def list_for_customer(
        self,
        customer_id: int,
    ) -> Sequence[Payment]:
        """Return all payments made by a customer."""

        result = await self.db.execute(
            select(Payment)
            .where(
                Payment.customer_id == customer_id
            )
            .order_by(
                Payment.created_at.desc()
            )
        )

        return result.scalars().all()


    # =========================================================
    # LIST PROVIDER PAYMENTS
    # =========================================================

    async def list_for_provider(
        self,
        provider_id: int,
    ) -> Sequence[Payment]:
        """Return all payments related to a provider."""

        result = await self.db.execute(
            select(Payment)
            .where(
                Payment.provider_id == provider_id
            )
            .order_by(
                Payment.created_at.desc()
            )
        )

        return result.scalars().all()


    # =========================================================
    # LIST ALL PAYMENTS
    # =========================================================

    async def list_all(
        self,
    ) -> Sequence[Payment]:
        """Return all payment records."""

        result = await self.db.execute(
            select(Payment)
            .order_by(
                Payment.created_at.desc()
            )
        )

        return result.scalars().all()


    # =========================================================
    # UPDATE STATUS
    # =========================================================

    async def update_status(
        self,
        payment: Payment,
        *,
        status: PaymentStatus,
        gateway_reference: str | None = None,
        failure_reason: str | None = None,
    ) -> Payment:
        """Update payment status and gateway information."""

        payment.status = status

        if gateway_reference is not None:
            payment.gateway_reference = (
                gateway_reference
            )

        if failure_reason is not None:
            payment.failure_reason = (
                failure_reason
            )

        await self.db.flush()

        return payment


    # =========================================================
    # UPDATE PAYMENT METHOD
    # =========================================================

    async def update_method(
        self,
        payment: Payment,
        payment_method: PaymentMethod,
    ) -> Payment:
        """Update the selected payment method."""

        payment.payment_method = (
            payment_method
        )

        await self.db.flush()

        return payment