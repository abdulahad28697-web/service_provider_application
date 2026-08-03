"""Business logic for administrative operations (user/provider management, audit)."""
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

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

    async def list_users(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        """Return a page of users."""
        return await self.users.list(skip=skip, limit=limit)

    async def list_providers(
        self, skip: int = 0, limit: int = 100, category: str | None = None
    ) -> Sequence[Provider]:
        """Return a page of providers, optionally filtered by category."""
        return await self.providers.list(skip=skip, limit=limit, category=category)

    async def verify_provider(
        self, provider_id: int, payload: ProviderVerifyRequest, admin: User
    ) -> Provider:
        """Toggle a provider's verification status and record an audit log."""
        provider = await self.providers.get(provider_id)
        if provider is None:
            raise NotFoundError("Provider not found.")

        updated = await self.providers.update_verification(provider, payload.is_verified)
        await self.logs.log_action(
            action="VERIFY_PROVIDER",
            performed_by=admin.id,
            details=f"Provider ID: {provider_id}, Business: {provider.business_name}, "
            f"Verified: {payload.is_verified}",
        )
        await self.db.commit()
        await self.db.refresh(updated)
        return updated

    async def audit_logs(self, skip: int = 0, limit: int = 100) -> Sequence[AdminLog]:
        """Return the administrative audit trail."""
        return await self.logs.list(skip=skip, limit=limit)
