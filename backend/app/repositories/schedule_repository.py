"""Data-access layer for provider schedules."""
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import DayOfWeek
from app.models.schedule import ProviderSchedule
from app.repositories.base import BaseRepository
from app.schemas.schedule import ScheduleSlot, ScheduleSlotUpdate


class ScheduleRepository(BaseRepository):
    """Queries for :class:`~app.models.schedule.ProviderSchedule`."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    async def get(self, schedule_id: int) -> Optional[ProviderSchedule]:
        """Return a schedule slot by primary key, or ``None``."""
        result = await self.db.execute(
            select(ProviderSchedule).where(ProviderSchedule.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_for_day(
        self, provider_id: int, day: DayOfWeek
    ) -> Optional[ProviderSchedule]:
        """Return a provider's slot for a specific weekday, or ``None``."""
        result = await self.db.execute(
            select(ProviderSchedule).where(
                ProviderSchedule.provider_id == provider_id,
                ProviderSchedule.day_of_week == day,
            )
        )
        return result.scalar_one_or_none()

    async def list(self, provider_id: int) -> Sequence[ProviderSchedule]:
        """Return all of a provider's slots, ordered by weekday."""
        result = await self.db.execute(
            select(ProviderSchedule)
            .where(ProviderSchedule.provider_id == provider_id)
            .order_by(ProviderSchedule.day_of_week)
        )
        return result.scalars().all()

    async def create(self, provider_id: int, slot: ScheduleSlot) -> ProviderSchedule:
        """Persist a new weekly slot for a provider."""
        schedule = ProviderSchedule(
            provider_id=provider_id,
            day_of_week=slot.day_of_week,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
        )
        self.db.add(schedule)
        await self.db.flush()
        return schedule

    async def update(
        self, schedule: ProviderSchedule, data: ScheduleSlotUpdate
    ) -> ProviderSchedule:
        """Apply the set fields of ``data`` onto ``schedule`` in place."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(schedule, field, value)
        await self.db.flush()
        return schedule

    async def delete(self, schedule: ProviderSchedule) -> None:
        """Remove a schedule slot from the database."""
        await self.db.delete(schedule)
        await self.db.flush()
