"""Business logic for administrative operations."""

import logging
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import UserRole
from app.core.exceptions import NotFoundError
from app.models.admin_log import AdminLog
from app.models.booking import Booking
from app.models.notification import Notification
from app.models.provider import Provider
from app.models.service import Service
from app.models.user import User
from app.repositories.admin_log_repository import AdminLogRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import ProviderVerifyRequest, UserRead

logger = logging.getLogger(__name__)


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

    async def get_provider_details(
        self,
        provider_id: int,
    ) -> Dict[str, Any]:
        """Return a provider with full details, owner user info, and counts for admins."""
        provider = await self.providers.get(provider_id)
        if provider is None:
            raise NotFoundError("Provider not found.")

        owner = await self.users.get(provider.user_id)
        service_count = await self.db.scalar(
            select(func.count(Service.id)).where(Service.provider_id == provider.id)
        ) or 0
        booking_count = await self.db.scalar(
            select(func.count(Booking.id)).where(Booking.provider_id == provider.id)
        ) or 0

        return {
            "id": provider.id,
            "user_id": provider.user_id,
            "business_name": provider.business_name,
            "description": provider.description,
            "category": provider.category,
            "hourly_rate": provider.hourly_rate,
            "rating": provider.rating,
            "is_verified": provider.is_verified,
            "city": provider.city,
            "address": provider.address,
            "created_at": provider.created_at,
            "updated_at": provider.updated_at,
            "owner": UserRead.model_validate(owner) if owner else None,
            "service_count": int(service_count),
            "booking_count": int(booking_count),
        }

    async def verify_provider(
        self,
        provider_id: int,
        payload: ProviderVerifyRequest,
        admin: User,
    ) -> Optional[Provider]:
        """Verify or reject a provider and update the owner's role."""
        logger.info(
            "Admin %s is verifying provider %s with is_verified=%s",
            admin.id,
            provider_id,
            payload.is_verified,
        )

        provider = await self.providers.get(provider_id)

        if provider is None:
            raise NotFoundError("Provider not found.")

        owner = await self.users.get(provider.user_id)

        if owner is None:
            raise NotFoundError("Provider account owner not found.")

        was_pending = not provider.is_verified
        provider_deleted = False
        business_name_saved = provider.business_name

        if payload.is_verified:
            provider.is_verified = True
            self.db.add(provider)
            new_role = UserRole.PROVIDER
            await self.users.update_role(owner, new_role)
            owner.is_verified = True
            self.db.add(owner)

            notification = Notification(
                user_id=owner.id,
                title="Provider Application Approved",
                message=(
                    f"Congratulations! Your application for '{provider.business_name}' "
                    "has been approved. You can now offer services and manage bookings."
                ),
                notification_type="provider_approved",
                is_read=False,
            )
            self.db.add(notification)
        else:
            new_role = UserRole.CUSTOMER
            await self.users.update_role(owner, new_role)
            owner.is_verified = False
            self.db.add(owner)

            notification = Notification(
                user_id=owner.id,
                title="Provider Application Update",
                message=(
                    f"Your provider application for '{business_name_saved}' "
                    "was reviewed and rejected by the platform administrator."
                ),
                notification_type="provider_rejected",
                is_read=False,
            )
            self.db.add(notification)

            if was_pending:
                booking_count = await self.db.scalar(
                    select(func.count(Booking.id)).where(
                        Booking.provider_id == provider.id
                    )
                )
                if (booking_count or 0) == 0:
                    # No dependent bookings — remove so the user can re-apply.
                    await self.db.delete(provider)
                    provider_deleted = True
                else:
                    # Keep the record when bookings exist (FK RESTRICT).
                    provider.is_verified = False
                    self.db.add(provider)
            else:
                provider.is_verified = False
                self.db.add(provider)

        await self.logs.log_action(
            action="VERIFY_PROVIDER",
            performed_by=admin.id,
            details=(
                f"Provider ID: {provider_id}, "
                f"Business: {business_name_saved}, "
                f"Verified: {payload.is_verified}, "
                f"New role: {new_role.value}"
            ),
        )

        await self.db.commit()

        if provider_deleted:
            logger.info("Provider %s was deleted upon rejection.", provider_id)
            return None

        await self.db.refresh(provider)
        logger.info(
            "Provider %s verification updated to %s.",
            provider_id,
            provider.is_verified,
        )
        return provider

    async def audit_logs(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AdminLog]:
        """Return the administrative audit trail."""
        return await self.logs.list(skip=skip, limit=limit)