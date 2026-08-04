"""Business logic for administrative operations."""

from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import UserRole
from app.core.exceptions import NotFoundError
from app.models.admin_log import AdminLog
from app.models.provider import Provider
from app.models.user import User
from app.repositories.admin_log_repository import AdminLogRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import ProviderVerifyRequest


class AdminService:
    """Encapsulates admin-only operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.providers = ProviderRepository(db)
        self.logs = AdminLogRepository(db)

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
    ) -> Sequence[Provider]:
        """Return providers, optionally filtered by category."""
        return await self.providers.list(
            skip=skip,
            limit=limit,
            category=category,
        )

    async def verify_provider(
        self,
        provider_id: int,
        payload: ProviderVerifyRequest,
        admin: User,
    ) -> Provider:
        """Verify or reject a provider and update the owner's role."""
        provider = await self.providers.get(provider_id)

        if provider is None:
            raise NotFoundError("Provider not found.")

        owner = await self.users.get(provider.user_id)

        if owner is None:
            raise NotFoundError("Provider account owner not found.")

        await self.providers.update_verification(
            provider,
            payload.is_verified,
        )

        new_role = (
            UserRole.PROVIDER
            if payload.is_verified
            else UserRole.CUSTOMER
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

        await self.db.commit()
        await self.db.refresh(provider)
        return provider

    async def audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AdminLog]:
        """Return the administrative audit trail."""
        return await self.logs.list(skip=skip, limit=limit)