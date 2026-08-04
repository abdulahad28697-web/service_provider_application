"""Schemas for user profiles, addresses, and favorite providers."""

from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from app.common.constants import UserRole


class UserProfileUpdate(BaseModel):
    """Editable user and profile fields."""

    full_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(
        default=None,
        min_length=7,
        max_length=30,
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=1000,
    )


class UserProfileRead(BaseModel):
    """Combined account and profile response."""

    user_id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AddressCreate(BaseModel):
    """Payload for creating an address."""

    label: str = Field(
        default="Home",
        min_length=1,
        max_length=50,
    )
    address_line_1: str = Field(
        ...,
        min_length=3,
        max_length=255,
    )
    address_line_2: Optional[str] = Field(
        default=None,
        max_length=255,
    )
    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )
    state_or_province: Optional[str] = Field(
        default=None,
        max_length=100,
    )
    postal_code: Optional[str] = Field(
        default=None,
        max_length=30,
    )
    country: str = Field(
        default="Pakistan",
        min_length=2,
        max_length=100,
    )
    is_default: bool = False


class AddressUpdate(BaseModel):
    """Payload for partially updating an address."""

    label: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    address_line_1: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=255,
    )
    address_line_2: Optional[str] = Field(
        default=None,
        max_length=255,
    )
    city: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    state_or_province: Optional[str] = Field(
        default=None,
        max_length=100,
    )
    postal_code: Optional[str] = Field(
        default=None,
        max_length=30,
    )
    country: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )
    is_default: Optional[bool] = None


class AddressRead(BaseModel):
    """Saved address response."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    user_id: int
    label: str
    address_line_1: str
    address_line_2: Optional[str]
    city: str
    state_or_province: Optional[str]
    postal_code: Optional[str]
    country: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class FavoriteProviderRead(BaseModel):
    """Favorite provider response."""

    id: int
    provider_id: int
    business_name: str
    category: str
    city: str
    rating: float
    hourly_rate: float
    created_at: datetime


class DeleteAccountRequest(BaseModel):
    """Password confirmation for account deletion."""

    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
    )