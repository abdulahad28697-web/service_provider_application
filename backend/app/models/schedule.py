"""ProviderSchedule ORM model.

A provider's weekly availability slot (one row per day of the week). A day is
uniquely identified by ``(provider_id, day_of_week)``; the start/end window may
cross midnight to represent overnight availability.
"""
from datetime import time

from sqlalchemy import Boolean, Enum, ForeignKey, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.common.constants import DayOfWeek
from app.database.base import Base, TimestampMixin


class ProviderSchedule(Base, TimestampMixin):
    """A provider's weekly availability slot (one row per day of the week)."""

    __tablename__ = "provider_schedules"
    __table_args__ = (
        UniqueConstraint("provider_id", "day_of_week", name="uq_schedule_provider_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("providers.id", ondelete="CASCADE"), index=True
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(Enum(DayOfWeek, name="day_of_week"))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    is_available: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:  # pragma: no cover - convenience only
        return (
            f"<ProviderSchedule id={self.id} day={self.day_of_week.value} "
            f"{self.start_time}-{self.end_time}>"
        )
