"""Review Pydantic schemas (create / read)."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    """Payload for leaving a review on a completed booking."""

    booking_id: int = Field(..., gt=0)
    rating: Decimal = Field(..., ge=1, le=5, description="Rating between 1 and 5.")
    comment: Optional[str] = Field(default="", max_length=1000)


class ReviewRead(BaseModel):
    """A review as returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    booking_id: int
    customer_id: int
    rating: Decimal
    comment: str
    created_at: datetime
