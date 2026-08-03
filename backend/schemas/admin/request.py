from pydantic import BaseModel, EmailStr
from schemas.admin.common import UserBase, ProviderBase

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProviderCreate(ProviderBase):
    pass

class ProviderVerifyRequest(BaseModel):
    is_verified: bool
