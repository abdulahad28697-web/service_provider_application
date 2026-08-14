"""Business logic for the booking lifecycle and provider schedules."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import (
    BookingStatus,
    BOOKING_STATUS_TRANSITIONS,
)
from app.common.pagination import Page, PageParams
from app.common.utils import generate_public_id, utc_now
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.booking import Booking
from app.models.provider import Provider
from app.models.schedule import ProviderSchedule
from app.models.user import User
from app.models.user_profile import UserProfile
from app.repositories.booking_repository import BookingRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.booking import (
    BookingCreate,
    BookingRead,
    BookingReschedule,
)
from app.schemas.schedule import (
    ScheduleSlot,
    ScheduleSlotRead,
    ScheduleSlotUpdate,
)
from app.services.notification_service import NotificationService
from app.services.scheduling_service import SchedulingService


class BookingService:
    """Encapsulates booking operations and their invariants."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

        self.bookings = BookingRepository(db)
        self.schedules = ScheduleRepository(db)
        self.providers = ProviderRepository(db)
        self.services = ServiceRepository(db)

        self.scheduling = SchedulingService(db)
        self.notifications = NotificationService(db)

    # ========================================================
    # CREATE BOOKING
    # ========================================================

    async def book(
        self,
        customer: User,
        data: BookingCreate,
    ) -> Booking:
        """Create a pending booking for a customer."""

        service = await self.services.get(
            data.service_id
        )

        if service is None or not service.is_active:
            raise NotFoundError(
                "Service not found."
            )

        end_time = (
            self.scheduling.compute_end_time(
                data.scheduled_start,
                service.duration_minutes,
            )
        )

        total_price = self._compute_price(
            service.price,
            service.price_unit,
            service.duration_minutes,
        )

        # Check provider availability and overlapping bookings.
        await self.scheduling.ensure_available(
            provider_id=service.provider_id,
            scheduled_date=data.scheduled_date,
            scheduled_start=data.scheduled_start,
            scheduled_end=end_time,
        )

        booking = await self.bookings.create(
            reference_code=generate_public_id(
                "BK-"
            ),
            service_id=service.id,
            customer_id=customer.id,
            provider_id=service.provider_id,
            service_title=service.title,
            scheduled_date=data.scheduled_date,
            scheduled_start=data.scheduled_start,
            scheduled_end=end_time,
            total_price=total_price,
            customer_notes=(
                data.customer_notes or ""
            ),
            location=(
                data.location or ""
            ),
        )

        provider = await self.providers.get(
            booking.provider_id
        )

        if provider is not None:
            await self.notifications.create(
                user_id=provider.user_id,
                title="New booking request",
                message=(
                    f"You received a new booking request for "
                    f"{booking.service_title} "
                    f"({booking.reference_code})."
                ),
                notification_type="booking_created",
                reference_id=booking.id,
            )

        await self.db.commit()
        await self.db.refresh(booking)

        await self.scheduling.publish_booking_event(
            "booking.created",
            booking.id,
            {
                "reference":
                    booking.reference_code
            },
        )

        return booking

    # ========================================================
    # GET ONE BOOKING
    # ========================================================

    async def get(
        self,
        booking_id: int,
        user: User,
    ) -> Booking:
        """
        Return a booking visible to the customer,
        provider or admin.
        """

        booking = await self.bookings.get(
            booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        await self._assert_visible(
            booking,
            user,
        )

        return booking

    # ========================================================
    # LIST BOOKING HISTORY
    # ========================================================

    async def list_history(
        self,
        user: User,
        params: PageParams,
        *,
        as_provider: Optional[bool] = None,
        status: Optional[BookingStatus] = None,
    ) -> Page[BookingRead]:
        """
        Return bookings belonging to the current user.

        Customer:
            returns customer's bookings.

        Provider:
            returns bookings for that provider profile.
        """

        customer_id = None
        provider_id = None

        if as_provider is True:
            provider = await self._provider_for(
                user
            )

            provider_id = provider.id

        elif as_provider is False:
            customer_id = user.id

        elif user.role.value == "provider":
            provider = await self._provider_for(
                user,
                strict=False,
            )

            provider_id = (
                provider.id
                if provider is not None
                else -1
            )

        elif user.role.value == "admin":
            # Admin may see everything.
            customer_id = None
            provider_id = None

        else:
            customer_id = user.id

        items, total = await self.bookings.list(
            params,
            customer_id=customer_id,
            provider_id=provider_id,
            status=status,
        )

        # Convert every booking into BookingRead
        # and include customer information.
        reads = [
            await self._to_read(booking)
            for booking in items
        ]

        return Page.create(
            reads,
            total,
            params.page,
            params.page_size,
        )

    # ========================================================
    # ACCEPT BOOKING
    # ========================================================

    async def accept(
        self,
        booking_id: int,
        provider: User,
    ) -> Booking:
        """Accept a pending booking."""

        booking = (
            await self._get_and_assert_provider(
                booking_id,
                provider,
            )
        )

        await self._transition(
            booking,
            BookingStatus.ACCEPTED,
        )

        # Recheck availability before final acceptance.
        await self.scheduling.ensure_available(
            provider_id=booking.provider_id,
            scheduled_date=booking.scheduled_date,
            scheduled_start=booking.scheduled_start,
            scheduled_end=booking.scheduled_end,
            exclude_booking_id=booking.id,
        )

        await self.notifications.create(
            user_id=booking.customer_id,
            title="Booking accepted",
            message=(
                f"Your booking for {booking.service_title} "
                f"({booking.reference_code}) was accepted."
            ),
            notification_type="booking_accepted",
            reference_id=booking.id,
        )

        await self.db.commit()
        await self.db.refresh(booking)

        await self.scheduling.publish_booking_event(
            "booking.accepted",
            booking.id,
            {
                "reference":
                    booking.reference_code
            },
        )

        return booking

    # ========================================================
    # REJECT BOOKING
    # ========================================================

    async def reject(
        self,
        booking_id: int,
        provider: User,
        reason: Optional[str],
    ) -> Booking:
        """Reject a pending booking."""

        booking = (
            await self._get_and_assert_provider(
                booking_id,
                provider,
            )
        )

        await self._transition(
            booking,
            BookingStatus.REJECTED,
        )

        booking.reject_reason = reason

        reject_message = (
            f"Your booking for {booking.service_title} "
            f"({booking.reference_code}) was rejected."
        )

        if reason:
            reject_message += f" Reason: {reason}"

        await self.notifications.create(
            user_id=booking.customer_id,
            title="Booking rejected",
            message=reject_message,
            notification_type="booking_rejected",
            reference_id=booking.id,
        )

        await self.db.commit()
        await self.db.refresh(booking)

        await self.scheduling.publish_booking_event(
            "booking.rejected",
            booking.id,
            {
                "reason": reason
            },
        )

        return booking

    # ========================================================
    # COMPLETE BOOKING
    # ========================================================

    async def complete(
        self,
        booking_id: int,
        provider: User,
    ) -> Booking:
        """Mark an accepted booking as completed."""

        booking = (
            await self._get_and_assert_provider(
                booking_id,
                provider,
            )
        )

        await self._transition(
            booking,
            BookingStatus.COMPLETED,
        )

        booking.completed_at = utc_now()

        await self.notifications.create(
            user_id=booking.customer_id,
            title="Booking completed",
            message=(
                f"Your booking for {booking.service_title} "
                f"({booking.reference_code}) was marked completed. "
                "You can now leave a review."
            ),
            notification_type="booking_completed",
            reference_id=booking.id,
        )

        await self.db.commit()
        await self.db.refresh(booking)

        await self.scheduling.publish_booking_event(
            "booking.completed",
            booking.id,
            {
                "reference":
                    booking.reference_code
            },
        )

        return booking

    # ========================================================
    # CANCEL BOOKING
    # ========================================================

    async def cancel(
        self,
        booking_id: int,
        user: User,
        reason: Optional[str],
    ) -> Booking:
        """Cancel a booking."""

        booking = await self.bookings.get(
            booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        if not await self._is_participant(
            booking,
            user,
        ):
            raise ForbiddenError(
                "You are not allowed to cancel this booking."
            )

        await self._transition(
            booking,
            BookingStatus.CANCELLED,
        )

        booking.cancel_reason = reason
        booking.cancelled_by = (
            user.role.value
        )

        # Notify the other participant about the cancellation.
        if user.id == booking.customer_id:
            provider = await self.providers.get(
                booking.provider_id
            )

            recipient_user_id = (
                provider.user_id
                if provider is not None
                else None
            )
        else:
            recipient_user_id = booking.customer_id

        if recipient_user_id is not None:
            cancel_message = (
                f"Booking {booking.reference_code} for "
                f"{booking.service_title} was cancelled."
            )

            if reason:
                cancel_message += f" Reason: {reason}"

            await self.notifications.create(
                user_id=recipient_user_id,
                title="Booking cancelled",
                message=cancel_message,
                notification_type="booking_cancelled",
                reference_id=booking.id,
            )

        await self.db.commit()
        await self.db.refresh(booking)

        await self.scheduling.publish_booking_event(
            "booking.cancelled",
            booking.id,
            {
                "reason": reason
            },
        )

        return booking

    # ========================================================
    # RESCHEDULE BOOKING
    # ========================================================

    async def reschedule(
        self,
        booking_id: int,
        customer: User,
        data: BookingReschedule,
    ) -> Booking:
        """
        Reschedule a customer's pending or accepted booking.

        Rules:
        - Only the booking customer may reschedule.
        - Only PENDING / ACCEPTED bookings may be rescheduled.
        - The service must still exist and be active.
        - The new time must fit provider availability.
        - Existing booking conflicts are checked while excluding
          this booking itself.
        """

        booking = await self.bookings.get(
            booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        if booking.customer_id != customer.id:
            raise ForbiddenError(
                "You are not allowed to reschedule this booking."
            )

        if booking.status not in {
            BookingStatus.PENDING,
            BookingStatus.ACCEPTED,
        }:
            raise ConflictError(
                "Only pending or accepted bookings can be rescheduled."
            )

        service = await self.services.get(
            booking.service_id
        )

        if service is None or not service.is_active:
            raise NotFoundError(
                "Service not found."
            )

        new_end_time = (
            self.scheduling.compute_end_time(
                data.scheduled_start,
                service.duration_minutes,
            )
        )

        await self.scheduling.ensure_available(
            provider_id=booking.provider_id,
            scheduled_date=data.scheduled_date,
            scheduled_start=data.scheduled_start,
            scheduled_end=new_end_time,
            exclude_booking_id=booking.id,
        )

        old_date = booking.scheduled_date
        old_start = booking.scheduled_start

        booking.scheduled_date = (
            data.scheduled_date
        )

        booking.scheduled_start = (
            data.scheduled_start
        )

        booking.scheduled_end = (
            new_end_time
        )

        await self.bookings.save(
            booking
        )

        provider = await self.providers.get(
            booking.provider_id
        )

        if provider is not None:
            await self.notifications.create(
                user_id=provider.user_id,
                title="Booking rescheduled",
                message=(
                    f"Booking {booking.reference_code} for "
                    f"{booking.service_title} was rescheduled "
                    f"from {old_date} at {old_start} to "
                    f"{booking.scheduled_date} at "
                    f"{booking.scheduled_start}."
                ),
                notification_type="booking_rescheduled",
                reference_id=booking.id,
            )

        await self.db.commit()
        await self.db.refresh(
            booking
        )

        await self.scheduling.publish_booking_event(
            "booking.rescheduled",
            booking.id,
            {
                "reference":
                    booking.reference_code,
                "scheduled_date":
                    str(booking.scheduled_date),
                "scheduled_start":
                    str(booking.scheduled_start),
                "scheduled_end":
                    str(booking.scheduled_end),
            },
        )

        return booking

    # ========================================================
    # PROVIDER SCHEDULE
    # ========================================================

    async def upsert_schedule(
        self,
        provider: User,
        slot: ScheduleSlot,
    ) -> ProviderSchedule:
        """Create/update weekly provider availability."""

        profile = await self._provider_for(
            provider
        )

        existing = (
            await self.schedules.get_for_day(
                profile.id,
                slot.day_of_week,
            )
        )

        if existing is not None:
            updated = await self.schedules.update(
                existing,
                ScheduleSlotUpdate(
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    is_available=slot.is_available,
                ),
            )

        else:
            updated = await self.schedules.create(
                profile.id,
                slot,
            )

        await self.db.commit()
        await self.db.refresh(updated)

        return updated

    async def list_schedules(
        self,
        provider: User,
    ) -> list[ScheduleSlotRead]:
        """Return provider schedule slots."""

        profile = await self._provider_for(
            provider
        )

        rows = await self.schedules.list(
            profile.id
        )

        return [
            ScheduleSlotRead.model_validate(
                row
            )
            for row in rows
        ]

    async def update_schedule(
        self,
        provider: User,
        schedule_id: int,
        data: ScheduleSlotUpdate,
    ) -> ProviderSchedule:
        """Update provider schedule slot."""

        schedule = (
            await self._schedule_or_404(
                provider,
                schedule_id,
            )
        )

        updated = await self.schedules.update(
            schedule,
            data,
        )

        await self.db.commit()
        await self.db.refresh(updated)

        return updated

    async def delete_schedule(
        self,
        provider: User,
        schedule_id: int,
    ) -> None:
        """Delete provider schedule slot."""

        schedule = (
            await self._schedule_or_404(
                provider,
                schedule_id,
            )
        )

        await self.schedules.delete(
            schedule
        )

        await self.db.commit()

    # ========================================================
    # HYDRATE BOOKING RESPONSE
    # ========================================================

    async def _to_read(
        self,
        booking: Booking,
    ) -> BookingRead:
        """
        Convert Booking ORM model into BookingRead and attach
        customer name, email and phone number.
        """

        read = BookingRead.model_validate(
            booking
        )

        result = await self.db.execute(
            select(
                User.full_name,
                User.email,
                UserProfile.phone_number,
            )
            .outerjoin(
                UserProfile,
                UserProfile.user_id == User.id,
            )
            .where(
                User.id == booking.customer_id
            )
        )

        customer = result.one_or_none()

        if customer is not None:
            read.customer_name = (
                customer.full_name
            )

            read.customer_email = (
                customer.email
            )

            read.customer_phone = (
                customer.phone_number
            )

        return read

    # ========================================================
    # PRICE
    # ========================================================

    def _compute_price(
        self,
        price,
        price_unit,
        duration_minutes,
    ):
        """Calculate booking price."""

        if price_unit.value == "per_hour":
            return (
                price * duration_minutes
            ) / 60

        return price

    # ========================================================
    # PROVIDER PROFILE
    # ========================================================

    async def _provider_for(
        self,
        user: User,
        strict: bool = True,
    ) -> Optional[Provider]:
        """Resolve provider profile for a user."""

        provider = (
            await self.providers.get_by_user_id(
                user.id
            )
        )

        if (
            provider is None
            and strict
        ):
            raise ForbiddenError(
                "A provider profile is required for this action."
            )

        return provider

    # ========================================================
    # PROVIDER OWNERSHIP
    # ========================================================

    async def _get_and_assert_provider(
        self,
        booking_id: int,
        user: User,
    ) -> Booking:
        """
        Return booking only if current provider owns it.
        """

        booking = await self.bookings.get(
            booking_id
        )

        if booking is None:
            raise NotFoundError(
                "Booking not found."
            )

        if user.role.value == "admin":
            return booking

        profile = await self._provider_for(
            user
        )

        if booking.provider_id != profile.id:
            raise ForbiddenError(
                "You are not the provider of this booking."
            )

        return booking

    # ========================================================
    # BOOKING VISIBILITY
    # ========================================================

    async def _assert_visible(
        self,
        booking: Booking,
        user: User,
    ) -> None:
        """
        Allow admin, booking customer or booking provider.
        """

        if user.role.value == "admin":
            return

        if booking.customer_id == user.id:
            return

        provider = await self._provider_for(
            user,
            strict=False,
        )

        if (
            provider is not None
            and booking.provider_id
            == provider.id
        ):
            return

        raise ForbiddenError(
            "You are not allowed to view this booking."
        )

    # ========================================================
    # BOOKING PARTICIPANT
    # ========================================================

    async def _is_participant(
        self,
        booking: Booking,
        user: User,
    ) -> bool:
        """Check whether user participates in booking."""

        if user.role.value == "admin":
            return True

        if booking.customer_id == user.id:
            return True

        provider = await self._provider_for(
            user,
            strict=False,
        )

        return (
            provider is not None
            and booking.provider_id
            == provider.id
        )

    # ========================================================
    # SCHEDULE OWNERSHIP
    # ========================================================

    async def _schedule_or_404(
        self,
        provider: User,
        schedule_id: int,
    ) -> ProviderSchedule:
        """Return schedule owned by provider."""

        profile = await self._provider_for(
            provider
        )

        schedule = await self.schedules.get(
            schedule_id
        )

        if (
            schedule is None
            or schedule.provider_id
            != profile.id
        ):
            raise NotFoundError(
                "Schedule slot not found."
            )

        return schedule

    # ========================================================
    # BOOKING STATUS TRANSITION
    # ========================================================

    async def _transition(
        self,
        booking: Booking,
        new_status: BookingStatus,
    ) -> None:
        """Move booking through allowed status transitions."""

        allowed = (
            BOOKING_STATUS_TRANSITIONS.get(
                booking.status,
                set(),
            )
        )

        if new_status not in allowed:
            raise ConflictError(
                "Cannot move a booking from "
                f"'{booking.status.value}' "
                f"to '{new_status.value}'."
            )

        booking.status = new_status