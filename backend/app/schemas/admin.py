"""Admin Pydantic schemas (provider onboarding/verification, audit logs)."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.constants import UserRole


class UserRead(BaseModel):
    """A user as returned to administrators."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class ProviderOnboard(BaseModel):
    """Payload for a provider to create their public profile."""

    business_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default="", max_length=1000)
    category: str = Field(..., min_length=1, max_length=120)
    hourly_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    city: Optional[str] = Field(default="", max_length=120)
    address: Optional[str] = Field(default="", max_length=255)


class ProviderRead(BaseModel):
    """A provider profile as returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    business_name: str = ""
    description: Optional[str] = ""
    category: Optional[str] = ""
    hourly_rate: Decimal = Decimal("0.00")
    rating: Decimal = Decimal("0.00")
    is_verified: bool = False
    city: Optional[str] = ""
    address: Optional[str] = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProviderDetailRead(ProviderRead):
    """Detailed provider application info with owner user and service statistics for admins."""

    owner: Optional[UserRead] = None
    service_count: int = 0
    booking_count: int = 0


class ProviderVerifyRequest(BaseModel):
    """Payload to verify/reject a provider profile."""

    is_verified: bool


class AdminLogRead(BaseModel):
    """An audit-log entry as returned to administrators."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    performed_by: Optional[int] = None
    details: str
    created_at: datetime

