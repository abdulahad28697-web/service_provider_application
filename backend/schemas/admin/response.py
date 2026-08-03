from pydantic import BaseModel, EmailStr
from datetime import datetime
from schemas.admin.common import UserBase, ProviderBase

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProviderResponse(ProviderBase):
    id: int
    user_id: int
    rating: float
    is_verified: bool
    user: UserResponse

    class Config:
        from_attributes = True

class AdminLogResponse(BaseModel):
    id: int
    action: str
    performed_by: int | None
    details: str | None
    created_at: datetime

    class Config:
        from_attributes = True
