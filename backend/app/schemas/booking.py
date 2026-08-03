"""Booking Pydantic schemas (request/response models)."""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.common.constants import BookingStatus
from app.common.pagination import Page


class BookingCreate(BaseModel):
    """Payload to book a service."""

    service_id: int = Field(..., gt=0)
    scheduled_date: date
    scheduled_start: time
    customer_notes: Optional[str] = Field(default="", max_length=2000)
    location: Optional[str] = Field(default="", max_length=255)

    @field_validator("scheduled_date")
    @classmethod
    def _date_not_in_past(cls, value: date) -> date:
        """A booking must not be scheduled in the past."""
        if value < date.today():
            raise ValueError("Scheduled date cannot be in the past.")
        return value


class BookingCreateResponse(BaseModel):
    """Returned immediately after a booking is created."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_code: str
    service_id: int
    status: BookingStatus
    total_price: Decimal
    scheduled_date: date
    scheduled_start: time
    scheduled_end: time
    message: Optional[str] = None


class BookingAction(BaseModel):
    """Reason payload for reject/cancel transitions."""

    reason: Optional[str] = Field(default=None, max_length=500)


class BookingRead(BaseModel):
    """A booking as returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_code: str
    service_id: int
    service_title: str
    customer_id: int
    provider_id: int
    scheduled_date: date
    scheduled_start: time
    scheduled_end: time
    status: BookingStatus
    customer_notes: str
    location: str
    total_price: Decimal
    cancelled_by: Optional[str] = None
    cancel_reason: Optional[str] = None
    reject_reason: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


BookingPage = Page[BookingRead]
