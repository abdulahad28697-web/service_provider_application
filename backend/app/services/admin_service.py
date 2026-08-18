"""Business logic for administrative operations."""

import logging
from typing import Optional, Sequence

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import UserRole
from app.core.exceptions import AppError, NotFoundError
from app.models.admin_log import AdminLog
from app.models.provider import Provider
from app.models.user import User
from app.repositories.admin_log_repository import AdminLogRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import ProviderVerifyRequest
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class AdminService:
    """Encapsulates admin-only operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.providers = ProviderRepository(db)
        self.logs = AdminLogRepository(db)
        self.notifications = NotificationService(db)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Return a page of users."""
        return await self.users.list(skip=skip, limit=limit)

    async def list_providers(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
        is_verified: bool | None = None,
    ) -> Sequence[Provider]:
        """Return providers, optionally filtered by category/verification."""
        return await self.providers.list(
            skip=skip,
            limit=limit,
            category=category,
            is_verified=is_verified,
        )

    async def get_provider_detail(
        self,
        provider_id: int,
    ) -> tuple[Provider, Optional[User]]:
        """Return a single provider with its account owner."""
        provider = await self.providers.get(provider_id)

        if provider is None:
            raise NotFoundError("Provider not found.")

        return provider, await self.users.get(provider.user_id)

    async def verify_provider(
        self,
        provider_id: int,
        payload: ProviderVerifyRequest,
        admin: User,
    ) -> tuple[Provider, User]:
        """Verify or reject a provider and update the owner's role."""
        provider = await self.providers.get(provider_id)

        if provider is None:
            raise NotFoundError("Provider not found.")

        owner = await self.users.get(provider.user_id)

        if owner is None:
            raise NotFoundError("Provider account owner not found.")

        new_role = (
            UserRole.PROVIDER
            if payload.is_verified
            else UserRole.CUSTOMER
        )

        try:
            await self.providers.update_verification(
                provider,
                payload.is_verified,
            )
            await self.users.update_role(owner, new_role)

            await self.logs.log_action(
                action="VERIFY_PROVIDER",
                performed_by=admin.id,
                details=(
                    f"Provider ID: {provider_id}, "
                    f"Business: {provider.business_name}, "
                    f"Verified: {payload.is_verified}, "
                    f"New role: {new_role.value}"
                ),
            )

            await self.notifications.create(
                user_id=owner.id,
                title=(
                    "Provider application approved"
                    if payload.is_verified
                    else "Provider application rejected"
                ),
                message=(
                    "Your provider profile has been verified. "
                    "You can now publish services."
                    if payload.is_verified
                    else (
                        "Your provider application was not approved. "
                        "Please contact support for details."
                    )
                ),
                notification_type="provider_verification",
                reference_id=provider.id,
            )

            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            logger.exception(
                "Failed to update verification for provider %s.",
                provider_id,
            )
            raise AppError(
                "Could not update the provider verification status.",
                code="provider_verification_failed",
            )

        await self.db.refresh(provider)
        await self.db.refresh(owner)

        logger.info(
            "Admin %s set provider %s is_verified=%s (owner role: %s).",
            admin.id,
            provider_id,
            payload.is_verified,
            new_role.value,
        )

        return provider, owner

    async def audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AdminLog]:
        """Return the administrative audit trail."""
        return await self.logs.list(skip=skip, limit=limit)