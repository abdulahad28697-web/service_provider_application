"""Authentication Pydantic schemas (register / login / tokens)."""
import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.constants import UserRole


class UserRegister(BaseModel):
    """Payload for creating a user account."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.CUSTOMER

    @field_validator("password")
    @classmethod
    def _password_strength(cls, value: str) -> str:
        """Enforce minimum password strength (8 chars + upper/lower/digit)."""
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one number.")
        return value


class UserLogin(BaseModel):
    """JSON login payload (alternative to the OAuth2 form)."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """An access token returned on successful authentication."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token claims."""

    user_id: str | None = None
