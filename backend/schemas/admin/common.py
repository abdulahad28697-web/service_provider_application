from pydantic import BaseModel, EmailStr
from datetime import datetime
from core.permissions import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.CLIENT

class ProviderBase(BaseModel):
    bio: str | None = None
    business_name: str | None = None
    category: str
    hourly_rate: float = 0.0

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str | None = None
