"""Data-access layer for users."""

from typing import Optional, Sequence

from sqlalchemy import select

from app.common.constants import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.auth import UserRegister


class UserRepository(BaseRepository):
    """Queries and persistence operations for users."""

    async def get(
        self,
        user_id: int,
    ) -> Optional[User]:
        """Return a user by primary key, or None."""
        result = await self.db.execute(
            select(User).where(
                User.id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> Optional[User]:
        """Return a user by normalized email, or None."""
        normalized_email = email.strip().lower()

        result = await self.db.execute(
            select(User).where(
                User.email == normalized_email
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        data: UserRegister,
        hashed_password: str,
    ) -> User:
        """Create a customer account with a hashed password."""
        user = User(
            email=str(data.email).strip().lower(),
            full_name=" ".join(
                data.full_name.split()
            ),
            hashed_password=hashed_password,
            role=UserRole.CUSTOMER,
            is_active=True,
        )

        self.db.add(user)
        await self.db.flush()

        return user

    async def update_password(
        self,
        user: User,
        hashed_password: str,
    ) -> User:
        """Update a user's password hash."""
        user.hashed_password = hashed_password

        self.db.add(user)
        await self.db.flush()

        return user

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Return users ordered from newest to oldest."""
        result = await self.db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()