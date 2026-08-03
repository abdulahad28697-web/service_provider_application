"""Scheduling logic and availability checks for bookings.

Responsibilities
----------------
* Derive a booking's end time from its start + service duration.
* Validate that a requested time slot falls inside the provider's weekly
  schedule and does not clash with an existing non-terminal booking.
* Publish booking lifecycle events to Redis so the notification agent can pick
  them up (Redis is optional; failures are swallowed so the booking still works
  when Redis is unavailable, e.g. in unit tests).
"""
from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import DAY_OF_WEEK_FROM_ISO
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.repositories.booking_repository import BookingRepository
from app.repositories.schedule_repository import ScheduleRepository


class SchedulingService:
    """Validate slot availability and publish booking events.

    ``compute_end_time`` is stateless and exposed as a static method; the
    availability checks need a session and therefore live on the instance.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.schedules = ScheduleRepository(db)
        self.bookings = BookingRepository(db)

    @staticmethod
    def compute_end_time(start: time, duration_minutes: int) -> time:
        """Return ``start`` + ``duration_minutes``, rolling past midnight if needed."""
        base = datetime.combine(date.today(), start) + timedelta(minutes=duration_minutes)
        return base.time()

    @staticmethod
    def _time_in_range(t: time, start: time, end: time) -> bool:
        """True if ``t`` is within [start, end). Handles overnight slots."""
        if start <= end:  # same-day window
            return start <= t < end
        # overnight window (e.g. 22:00 -> 02:00)
        return t >= start or t < end

    async def provider_available(
        self,
        *,
        provider_id: int,
        scheduled_date: date,
        scheduled_start: time,
        scheduled_end: time,
        strict: bool = False,
    ) -> bool:
        """Return True if the provider is *open* for the requested slot.

        This checks the provider's weekly schedule only — it does NOT check
        whether the slot is already taken (see :meth:`ensure_available`, which
        calls both).

        ``strict=True`` treats a day with *no configured schedule* as
        unavailable; the default is lenient (no schedule -> available) so the
        platform still works for providers who have not set up a weekly schedule
        yet.
        """
        weekday = DAY_OF_WEEK_FROM_ISO[scheduled_date.weekday()]
        schedule = await self.schedules.get_for_day(provider_id, weekday)

        if schedule is None:
            return not strict
        if not schedule.is_available:
            return False

        covers_start = self._time_in_range(
            scheduled_start, schedule.start_time, schedule.end_time
        )
        covers_end = self._time_in_range(
            scheduled_end, schedule.start_time, schedule.end_time
        )
        return covers_start and covers_end

    async def ensure_available(
        self,
        *,
        provider_id: int,
        scheduled_date: date,
        scheduled_start: time,
        scheduled_end: time,
        strict: bool = False,
        exclude_booking_id: Optional[int] = None,
    ) -> None:
        """Raise :class:`BadRequestError` unless the slot is open AND free.

        Used both at booking creation and again when a provider accepts, so a
        slot that became busy in the meantime cannot sneak through. The conflict
        check runs unconditionally (even in lenient mode) so overlapping
        bookings are always rejected.
        """
        if not await self.provider_available(
            provider_id=provider_id,
            scheduled_date=scheduled_date,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            strict=strict,
        ):
            raise BadRequestError("The provider is not available at the requested time.")

        conflicts = await self.bookings.count_overlaps(
            provider_id=provider_id,
            scheduled_date=scheduled_date,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            exclude_booking_id=exclude_booking_id,
        )
        if conflicts:
            raise BadRequestError("This time slot is already booked.")

    # ------------------------------------------------------------------ #
    # Redis event publishing (for the notification agent)
    # ------------------------------------------------------------------ #
    @staticmethod
    async def publish_booking_event(event: str, booking_id: int, payload: dict) -> None:
        """Best-effort publish of a booking event to Redis.

        Never raises: a failure here must not fail the booking request. The
        notification agent (another team's module) subscribes to this channel.
        """
        if not settings.ENABLE_REDIS:
            return
        try:
            import json

            import redis.asyncio as aioredis

            client = aioredis.from_url(settings.REDIS_URL)
            await client.publish(
                settings.NOTIFICATION_CHANNEL,
                json.dumps({"event": event, "booking_id": booking_id, **payload}),
            )
            await client.aclose()
        except Exception:  # pragma: no cover - redis is best-effort
            pass
