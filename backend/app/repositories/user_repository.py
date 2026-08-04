"""Data-access layer for users."""

from typing import Optional, Sequence

from sqlalchemy import func, select

from app.common.constants import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.auth import UserRegister


class UserRepository(BaseRepository):
    """Database operations for users."""

    async def get(
        self,
        user_id: int,
    ) -> Optional[User]:
        """Return a user by primary key."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> Optional[User]:
        """Return a user by case-insensitive email."""
        normalized_email = email.strip().lower()

        result = await self.db.execute(
            select(User).where(
                func.lower(User.email) == normalized_email
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        data: UserRegister,
        hashed_password: str,
    ) -> User:
        """Create and persist a new customer account."""
        user = User(
            email=data.email.strip().lower(),
            full_name=data.full_name.strip(),
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
        """Replace a user's password hash."""
        user.hashed_password = hashed_password

        self.db.add(user)
        await self.db.flush()
        return user

    async def update_profile(
        self,
        user: User,
        *,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
    ) -> User:
        """Update basic user account fields."""
        if full_name is not None:
            user.full_name = full_name.strip()

        if email is not None:
            user.email = email.strip().lower()

        self.db.add(user)
        await self.db.flush()
        return user

    async def deactivate(
        self,
        user: User,
    ) -> User:
        """Deactivate a user account without deleting its history."""
        user.is_active = False

        self.db.add(user)
        await self.db.flush()
        return user

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Return users ordered by creation date."""
        result = await self.db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_role(
        self,
        user: User,
        role: UserRole,
    ) -> User:
        """Update a user's platform role."""
        user.role = role

        self.db.add(user)
        await self.db.flush()
        return user