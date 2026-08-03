"""Provider schedule Pydantic schemas (request/response models)."""
from datetime import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator

from app.common.constants import DayOfWeek


class ScheduleSlot(BaseModel):
    """A weekly availability slot for a provider."""

    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    is_available: bool = True

    @model_validator(mode="after")
    def _end_after_start(self) -> "ScheduleSlot":
        """Guard against inverted time windows (same-day slots only)."""
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time.")
        return self


class ScheduleSlotUpdate(BaseModel):
    """Partial update for a schedule slot."""

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_available: Optional[bool] = None


class ScheduleSlotRead(ScheduleSlot):
    """A schedule slot as returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
