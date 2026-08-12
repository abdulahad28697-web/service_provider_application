"""Authentication Pydantic schemas."""

import re
from app.common.constants import UserRole
from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_password_strength(value: str) -> str:
    """Require at least one lowercase, uppercase, and numeric character."""
    if not re.search(r"[a-z]", value):
        raise ValueError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(r"[A-Z]", value):
        raise ValueError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(r"[0-9]", value):
        raise ValueError(
            "Password must contain at least one number."
        )

    return value


class UserRegister(BaseModel):
    """Payload for creating a customer or provider account."""

    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    role: UserRole = UserRole.CUSTOMER

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class UserLogin(BaseModel):
    """JSON login payload."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """An access token returned after authentication."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token claims."""

    user_id: str | None = None


class ChangePasswordRequest(BaseModel):
    """Payload for changing an authenticated user's password."""

    current_password: str
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    @field_validator("new_password")
    @classmethod
    def _new_password_strength(cls, value: str) -> str:
        return validate_password_strength(value)


class ForgotPasswordRequest(BaseModel):
    """Payload for requesting password-reset instructions."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Payload for resetting a password with a reset token."""

    reset_token: str = Field(..., min_length=1)
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    @field_validator("new_password")
    @classmethod
    def _reset_password_strength(cls, value: str) -> str:
        return validate_password_strength(value)