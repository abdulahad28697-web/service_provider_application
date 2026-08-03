"""Business logic for provider profiles (onboarding)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.provider import Provider
from app.models.user import User
from app.repositories.provider_repository import ProviderRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import ProviderOnboard


class ProviderService:
    """Encapsulates provider-profile operations and their invariants."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.providers = ProviderRepository(db)
        self.users = UserRepository(db)

    async def onboard(self, user: User, data: ProviderOnboard) -> Provider:
        """Create a provider profile for a provider-role user."""
        if user.role.value != "provider":
            raise NotFoundError("Only provider accounts can create a provider profile.")
        if await self.providers.get_by_user_id(user.id):
            raise ConflictError("A provider profile already exists for this user.")
        provider = await self.providers.create(user.id, data)
        await self.db.commit()
        await self.db.refresh(provider)
        return provider
