"""Business logic for authentication."""

from typing import Optional

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    UnauthorizedError,
)
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ChangePasswordRequest,
    ResetPasswordRequest,
    UserRegister,
)
from app.services.email_service import EmailService


class AuthService:
    """Registration, login, and password-management rules."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.email_service = EmailService()

    async def register(
        self,
        data: UserRegister,
    ) -> User:
        """Register a customer using a unique email."""
        if await self.users.get_by_email(
            str(data.email)
        ):
            raise ConflictError(
                "A user with this email already exists."
            )

        user = await self.users.create(
            data,
            hash_password(data.password),
        )

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> User:
        """Validate credentials and return an active user."""
        user = await self.users.get_by_email(email)

        if (
            user is None
            or not verify_password(
                password,
                user.hashed_password,
            )
        ):
            raise UnauthorizedError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise UnauthorizedError(
                "User account is inactive."
            )

        return user

    def issue_token(
        self,
        user: User,
    ) -> str:
        """Issue a signed JWT access token."""
        return create_access_token(
            subject=str(user.id),
            role=user.role.value,
        )

    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> None:
        """Change an authenticated user's password."""
        if not verify_password(
            data.current_password,
            user.hashed_password,
        ):
            raise BadRequestError(
                "Current password is incorrect."
            )

        if verify_password(
            data.new_password,
            user.hashed_password,
        ):
            raise BadRequestError(
                "New password must be different."
            )

        await self.users.update_password(
            user,
            hash_password(data.new_password),
        )

        await self.db.commit()

    async def request_password_reset(
        self,
        email: str,
    ) -> Optional[str]:
        """Generate a reset token and dispatch verification email to the user."""
        user = await self.users.get_by_email(email)

        if user is None or not user.is_active:
            return None

        token = create_password_reset_token(
            subject=str(user.id)
        )

        self.email_service.send_password_reset_email(
            to_email=user.email,
            full_name=user.full_name,
            reset_token=token,
        )

        return token

    async def reset_password(
        self,
        data: ResetPasswordRequest,
    ) -> None:
        """Reset a password using a valid short-lived token."""
        try:
            payload = decode_password_reset_token(
                data.reset_token
            )

        except jwt.ExpiredSignatureError as error:
            raise BadRequestError(
                "Password-reset token has expired."
            ) from error

        except jwt.PyJWTError as error:
            raise BadRequestError(
                "Invalid password-reset token."
            ) from error

        user_id = payload.get("sub")

        if user_id is None:
            raise BadRequestError(
                "Invalid password-reset token."
            )

        try:
            user = await self.users.get(int(user_id))

        except (TypeError, ValueError) as error:
            raise BadRequestError(
                "Invalid password-reset token."
            ) from error

        if user is None or not user.is_active:
            raise BadRequestError(
                "Invalid password-reset token."
            )

        if verify_password(
            data.new_password,
            user.hashed_password,
        ):
            raise BadRequestError(
                "New password must be different."
            )

        await self.users.update_password(
            user,
            hash_password(data.new_password),
        )

        await self.db.commit()