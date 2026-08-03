"""Service Pydantic schemas (request/response models)."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import PriceUnit
from app.common.pagination import Page


class ServiceBase(BaseModel):
    """Shared fields for create/read of a service."""

    category_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = Field(default=None, max_length=220)
    description: Optional[str] = Field(default="", max_length=5000)
    price: Decimal = Field(default=Decimal("0"), ge=0)
    price_unit: PriceUnit = PriceUnit.PER_HOUR
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    is_active: bool = True
    is_featured: bool = False
    images: List[str] = Field(default_factory=list)


class ServiceCreate(ServiceBase):
    """Payload for creating a service (provider_id comes from the current user)."""


class ServiceUpdate(BaseModel):
    """Payload for updating a service; all fields optional."""

    category_id: Optional[int] = Field(default=None, gt=0)
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    slug: Optional[str] = Field(default=None, max_length=220)
    description: Optional[str] = Field(default=None, max_length=5000)
    price: Optional[Decimal] = Field(default=None, ge=0)
    price_unit: Optional[PriceUnit] = None
    duration_minutes: Optional[int] = Field(default=None, ge=1, le=1440)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    images: Optional[List[str]] = None


class ServiceRead(BaseModel):
    """A service as returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

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
    # Rich fields populated by the service layer when requested.
    category_name: Optional[str] = None
    provider_name: Optional[str] = None


ServicePage = Page[ServiceRead]
