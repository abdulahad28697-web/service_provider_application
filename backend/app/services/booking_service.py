"""Business logic for the booking lifecycle and provider schedules."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import BookingStatus, BOOKING_STATUS_TRANSITIONS
from app.common.pagination import Page, PageParams
from app.common.utils import generate_public_id, utc_now
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.booking import Booking
from app.models.provider import Provider
from app.models.schedule import ProviderSchedule
from app.models.user import User
from app.repositories.booking_repository import BookingRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.booking import BookingCreate, BookingRead
from app.schemas.schedule import ScheduleSlot, ScheduleSlotRead, ScheduleSlotUpdate
from app.services.scheduling_service import SchedulingService


class BookingService:
    """Encapsulates booking operations and their invariants."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.bookings = BookingRepository(db)
        self.schedules = ScheduleRepository(db)
        self.providers = ProviderRepository(db)
        self.services = ServiceRepository(db)
        self.scheduling = SchedulingService(db)

    # ------------------------------------------------------------------ #
    # Bookings
    # ------------------------------------------------------------------ #
    async def book(self, customer: User, data: BookingCreate) -> Booking:
        """Create a pending booking for a customer."""
        service = await self.services.get(data.service_id)
        if service is None or not service.is_active:
            raise NotFoundError("Service not found.")

        end_time = self.scheduling.compute_end_time(
            data.scheduled_start, service.duration_minutes
        )
        total_price = self._compute_price(
            service.price, service.price_unit, service.duration_minutes
        )

        await self.scheduling.ensure_available(
            provider_id=service.provider_id,
            scheduled_date=data.scheduled_date,
            scheduled_start=data.scheduled_start,
            scheduled_end=end_time,
        )

        booking = await self.bookings.create(
            reference_code=generate_public_id("BK-"),
            service_id=service.id,
            customer_id=customer.id,
            provider_id=service.provider_id,
            service_title=service.title,
            scheduled_date=data.scheduled_date,
            scheduled_start=data.scheduled_start,
            scheduled_end=end_time,
            total_price=total_price,
            customer_notes=data.customer_notes or "",
            location=data.location or "",
        )
        await self.db.commit()
        await self.db.refresh(booking)

        await self.scheduling.publish_booking_event(
            "booking.created", booking.id, {"reference": booking.reference_code}
        )
        return booking

    async def get(self, booking_id: int, user: User) -> Booking:
        """Return a booking visible to ``user``, else ``NotFoundError``/``ForbiddenError``."""
        booking = await self.bookings.get(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found.")
        await self._assert_visible(booking, user)
        return booking

    async def list_history(
        self,
        user: User,
        params: PageParams,
        *,
        as_provider: Optional[bool] = None,
        status: Optional[BookingStatus] = None,
    ) -> Page[BookingRead]:
        """Return bookings the user is involved in (as customer or provider)."""
        customer_id, provider_id = None, None
        if as_provider is True:
            provider_id = (await self._provider_for(user)).id
        elif as_provider is False:
            customer_id = user.id
        elif user.role.value == "provider":
            # Providers see their provider bookings; admins see everything.
            provider = await self._provider_for(user, strict=False)
            provider_id = provider.id if provider is not None else -1  # -1: none
        else:
            customer_id = user.id

        items, total = await self.bookings.list(
            params,
            customer_id=customer_id,
            provider_id=provider_id,
            status=status,
        )
        return Page.create(list(items), total, params.page, params.page_size)

    async def accept(self, booking_id: int, provider: User) -> Booking:
        """Accept a booking, re-verifying the slot is still free."""
        booking = await self._get_and_assert_provider(booking_id, provider)
        await self._transition(booking, BookingStatus.ACCEPTED)

        # Final availability gate: the slot must still be free at acceptance
        # time, excluding this very booking from the conflict check.
        await self.scheduling.ensure_available(
            provider_id=booking.provider_id,
            scheduled_date=booking.scheduled_date,
            scheduled_start=booking.scheduled_start,
            scheduled_end=booking.scheduled_end,
            exclude_booking_id=booking.id,
        )

        await self.db.commit()
        await self.db.refresh(booking)
        await self.scheduling.publish_booking_event(
            "booking.accepted", booking.id, {"reference": booking.reference_code}
        )
        return booking

    async def reject(
        self, booking_id: int, provider: User, reason: Optional[str]
    ) -> Booking:
        """Reject a booking with an optional reason."""
        booking = await self._get_and_assert_provider(booking_id, provider)
        await self._transition(booking, BookingStatus.REJECTED)
        booking.reject_reason = reason
        await self.db.commit()
        await self.db.refresh(booking)
        await self.scheduling.publish_booking_event(
            "booking.rejected", booking.id, {"reason": reason}
        )
        return booking

    async def complete(self, booking_id: int, provider: User) -> Booking:
        """Mark an accepted booking as completed."""
        booking = await self._get_and_assert_provider(booking_id, provider)
        await self._transition(booking, BookingStatus.COMPLETED)
        booking.completed_at = utc_now()
        await self.db.commit()
        await self.db.refresh(booking)
        await self.scheduling.publish_booking_event(
            "booking.completed", booking.id, {"reference": booking.reference_code}
        )
        return booking

    async def cancel(
        self, booking_id: int, user: User, reason: Optional[str]
    ) -> Booking:
        """Cancel a booking (by the customer, its provider, or an admin)."""
        booking = await self.bookings.get(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found.")

        if not await self._is_participant(booking, user):
            raise ForbiddenError("You are not allowed to cancel this booking.")

        await self._transition(booking, BookingStatus.CANCELLED)
        booking.cancel_reason = reason
        booking.cancelled_by = user.role.value
        await self.db.commit()
        await self.db.refresh(booking)
        await self.scheduling.publish_booking_event(
            "booking.cancelled", booking.id, {"reason": reason}
        )
        return booking

    # ------------------------------------------------------------------ #
    # Provider schedule management
    # ------------------------------------------------------------------ #
    async def upsert_schedule(
        self, provider: User, slot: ScheduleSlot
    ) -> ProviderSchedule:
        """Create or replace the provider's weekly slot for the given day."""
        profile = await self._provider_for(provider)
        existing = await self.schedules.get_for_day(profile.id, slot.day_of_week)
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
            updated = await self.schedules.create(profile.id, slot)
        await self.db.commit()
        await self.db.refresh(updated)
        return updated

    async def list_schedules(self, provider: User) -> list[ScheduleSlotRead]:
        """Return all weekly slots for the acting provider."""
        profile = await self._provider_for(provider)
        rows = await self.schedules.list(profile.id)
        return [ScheduleSlotRead.model_validate(r) for r in rows]

    async def update_schedule(
        self, provider: User, schedule_id: int, data: ScheduleSlotUpdate
    ) -> ProviderSchedule:
        """Update one of the provider's slots."""
        schedule = await self._schedule_or_404(provider, schedule_id)
        updated = await self.schedules.update(schedule, data)
        await self.db.commit()
        await self.db.refresh(updated)
        return updated

    async def delete_schedule(self, provider: User, schedule_id: int) -> None:
        """Delete one of the provider's slots."""
        schedule = await self._schedule_or_404(provider, schedule_id)
        await self.schedules.delete(schedule)
        await self.db.commit()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _compute_price(self, price, price_unit, duration_minutes):
        """Resolve the booking price from the service's unit and duration.

        Hourly services are prorated by duration; fixed/visit prices pass
        through unchanged.
        """
        if price_unit.value == "per_hour":
            return (price * duration_minutes) / 60
        return price

    async def _provider_for(self, user: User, strict: bool = True) -> Optional[Provider]:
        """Resolve the provider profile for ``user``, raising if required."""
        provider = await self.providers.get_by_user_id(user.id)
        if provider is None and strict:
            raise ForbiddenError("A provider profile is required for this action.")
        return provider

    async def _get_and_assert_provider(self, booking_id: int, user: User) -> Booking:
        """Return a booking the acting provider is allowed to manage."""
        booking = await self.bookings.get(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found.")
        profile = await self._provider_for(user)
        if booking.provider_id != profile.id and user.role.value != "admin":
            raise ForbiddenError("You are not the provider of this booking.")
        return booking

    async def _assert_visible(self, booking: Booking, user: User) -> None:
        """Raise unless ``user`` is an admin, the customer, or the provider."""
        if user.role.value == "admin":
            return
        if booking.customer_id == user.id:
            return
        provider = await self._provider_for(user, strict=False)
        if provider is not None and booking.provider_id == provider.id:
            return
        raise ForbiddenError("You are not allowed to view this booking.")

    async def _is_participant(self, booking: Booking, user: User) -> bool:
        """True if ``user`` is an admin, the customer, or the booking's provider."""
        if user.role.value == "admin":
            return True
        if booking.customer_id == user.id:
            return True
        provider = await self._provider_for(user, strict=False)
        return provider is not None and booking.provider_id == provider.id

    async def _schedule_or_404(self, provider: User, schedule_id: int) -> ProviderSchedule:
        """Return a schedule slot owned by ``provider``, else ``NotFoundError``."""
        profile = await self._provider_for(provider)
        schedule = await self.schedules.get(schedule_id)
        if schedule is None or schedule.provider_id != profile.id:
            raise NotFoundError("Schedule slot not found.")
        return schedule

    async def _transition(self, booking: Booking, new_status: BookingStatus) -> None:
        """Move a booking to ``new_status``, enforcing the state machine."""
        allowed = BOOKING_STATUS_TRANSITIONS.get(booking.status, set())
        if new_status not in allowed:
            raise ConflictError(
                f"Cannot move a booking from '{booking.status.value}' to '{new_status.value}'."
            )
        booking.status = new_status
