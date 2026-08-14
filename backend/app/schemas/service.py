"""Service Pydantic schemas (request/response models)."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import PriceUnit
from app.common.pagination import Page


# ============================================================
# BASE SERVICE SCHEMA
# ============================================================


class ServiceBase(BaseModel):
    """Shared fields for creating and reading a service."""

    # Provider can either provide an existing category ID
    # or type a category name manually.
    category_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    category_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )

    slug: Optional[str] = Field(
        default=None,
        max_length=220,
    )

    description: Optional[str] = Field(
        default="",
        max_length=5000,
    )

    price: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    price_unit: PriceUnit = PriceUnit.PER_HOUR

    duration_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
    )

    is_active: bool = True

    is_featured: bool = False

    images: List[str] = Field(
        default_factory=list,
    )


# ============================================================
# CREATE SERVICE
# ============================================================


class ServiceCreate(ServiceBase):
    """
    Payload for creating a service.

    provider_id is NOT accepted from the frontend.
    It is determined from the authenticated provider.
    """

    pass


# ============================================================
# UPDATE SERVICE
# ============================================================


class ServiceUpdate(BaseModel):
    """Payload for updating a service."""

    category_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    category_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    slug: Optional[str] = Field(
        default=None,
        max_length=220,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=5000,
    )

    price: Optional[Decimal] = Field(
        default=None,
        ge=0,
    )

    price_unit: Optional[PriceUnit] = None

    duration_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=1440,
    )

    is_active: Optional[bool] = None

    is_featured: Optional[bool] = None

    images: Optional[List[str]] = None


# ============================================================
# READ / RESPONSE SERVICE
# ============================================================


class ServiceRead(BaseModel):
    """Service information returned by the API."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    category_id: int

    provider_id: int

    title: str

    slug: str

    description: str

    price: Decimal

    price_unit: PriceUnit

    duration_minutes: int

    is_active: bool

    is_featured: bool

    images: List[str]

    created_at: datetime

    # --------------------------------------------------------
    # HYDRATED FIELDS
    # --------------------------------------------------------

    category_name: Optional[str] = None

    provider_name: Optional[str] = None

    # Average rating of the provider.
    provider_rating: float = 0.0

    # Total number of reviews received by the provider.
    review_count: int = 0


# ============================================================
# PAGINATION
# ============================================================


ServicePage = Page[ServiceRead]