"""Data-access layer for users."""
from typing import Optional, Sequence

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.auth import UserRegister


class UserRepository(BaseRepository):
    """Queries for :class:`~app.models.user.User`."""

    async def get(self, user_id: int) -> Optional[User]:
        """Return a user by primary key, or ``None`` if absent."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Return a user by (case-insensitive) email, or ``None`` if absent."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, data: UserRegister, hashed_password: str) -> User:
        """Persist a new user with a pre-hashed password."""
        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hashed_password,
            role=data.role,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        """Return a page of users ordered by creation time."""
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()
