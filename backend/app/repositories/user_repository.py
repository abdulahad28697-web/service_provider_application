"""Data-access layer for users."""
from typing import Optional

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


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
