from enum import Enum
from fastapi import HTTPException, status

class UserRole(str, Enum):
    ADMIN = "admin"
    PROVIDER = "provider"
    CLIENT = "client"

class PermissionChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user_role: str):
        if current_user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
        return True
