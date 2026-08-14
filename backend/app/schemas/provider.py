"""Schemas for provider profiles, portfolio, statistics and public profiles."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.common.constants import PriceUnit


# ============================================================
# PROVIDER PROFILE UPDATE
# ============================================================


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


# ============================================================
# PORTFOLIO
# ============================================================


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
        from_attributes=True,
    )

    id: int
    provider_id: int
    image_url: str
    caption: Optional[str]
    created_at: datetime


# ============================================================
# PROVIDER STATISTICS
# ============================================================


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


# ============================================================
# PUBLIC PROVIDER SERVICE
# ============================================================


class ProviderPublicServiceRead(BaseModel):
    """
    A service displayed on the public provider profile.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    category_id: int

    category_name: Optional[str] = None

    title: str

    slug: str

    description: str

    price: Decimal

    price_unit: PriceUnit

    duration_minutes: int

    is_featured: bool

    images: List[str]

    created_at: datetime


# ============================================================
# PUBLIC PROVIDER REVIEW
# ============================================================


class ProviderPublicReviewRead(BaseModel):
    """Review displayed on a provider's public profile."""

    id: int

    booking_id: int

    customer_id: int

    customer_name: Optional[str] = None

    rating: Decimal

    comment: str

    created_at: datetime


# ============================================================
# PUBLIC PROVIDER PROFILE
# ============================================================


class ProviderPublicRead(BaseModel):
    """
    Complete public provider profile displayed to customers.
    """

    id: int

    user_id: int

    provider_name: str

    business_name: str

    description: str

    category: str

    hourly_rate: Decimal

    city: str

    address: str

    is_verified: bool

    average_rating: Decimal

    review_count: int

    portfolio: List[PortfolioImageRead] = Field(
        default_factory=list,
    )

    services: List[ProviderPublicServiceRead] = Field(
        default_factory=list,
    )

    reviews: List[ProviderPublicReviewRead] = Field(
        default_factory=list,
    )