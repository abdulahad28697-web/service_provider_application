"""Business logic for authentication (registration and login)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import UserRole
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister


class AuthService:
    """Encapsulates registration and authentication rules."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)

    async def register(self, data: UserRegister) -> User:
        """Register a new user, enforcing a unique email."""
        if await self.users.get_by_email(data.email):
            raise ConflictError("A user with this email already exists.")
        user = await self.users.create(data, hash_password(data.password))
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User:
        """Validate credentials and return the matching active user."""
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedError("User account is inactive.")
        return user

    def issue_token(self, user: User) -> str:
        """Issue a signed JWT for a user."""
        return create_access_token(subject=str(user.id), role=user.role.value)
