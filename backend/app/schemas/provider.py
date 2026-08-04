"""Schemas for provider self-service, portfolio, and statistics."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ProviderProfileUpdate(BaseModel):
    """Editable provider-profile fields."""

    business_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
    )
    category: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=120,
    )
    hourly_rate: Optional[Decimal] = Field(
        default=None,
        ge=0,
    )
    city: Optional[str] = Field(
        default=None,
        max_length=120,
    )
    address: Optional[str] = Field(
        default=None,
        max_length=255,
    )


class PortfolioImageCreate(BaseModel):
    """Payload for adding a portfolio image URL."""

    image_url: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )
    caption: Optional[str] = Field(
        default=None,
        max_length=255,
    )


class PortfolioImageRead(BaseModel):
    """Provider portfolio image response."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    provider_id: int
    image_url: str
    caption: Optional[str]
    created_at: datetime


class ProviderStatisticsRead(BaseModel):
    """Provider activity and earnings statistics."""

    provider_id: int
    total_services: int
    total_bookings: int
    pending_bookings: int
    accepted_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    total_revenue: Decimal
    average_rating: Decimal
    portfolio_images: int