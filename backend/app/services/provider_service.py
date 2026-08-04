"""Business logic for provider profiles and portfolios."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import UserRole
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from app.models.provider import Provider
from app.models.user import User
from app.repositories.provider_repository import (
    ProviderRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.admin import ProviderOnboard
from app.schemas.provider import (
    PortfolioImageCreate,
    ProviderProfileUpdate,
    ProviderStatisticsRead,
)


class ProviderService:
    """Provider application and profile-management rules."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db
        self.providers = ProviderRepository(db)
        self.users = UserRepository(db)

    async def apply(
        self,
        user: User,
        data: ProviderOnboard,
    ) -> Provider:
        """Create a pending provider application."""
        if user.role == UserRole.ADMIN:
            raise BadRequestError(
                "Administrators cannot apply as providers."
            )

        if await self.providers.get_by_user_id(
            user.id
        ):
            raise ConflictError(
                "A provider profile already exists for this user."
            )

        provider = await self.providers.create(
            user.id,
            data,
        )

        await self.db.commit()
        await self.db.refresh(provider)

        return provider

    async def onboard(
        self,
        user: User,
        data: ProviderOnboard,
    ) -> Provider:
        """Legacy onboarding for an existing provider-role user."""
        if user.role != UserRole.PROVIDER:
            raise NotFoundError(
                "Only provider accounts can create a provider profile."
            )

        if await self.providers.get_by_user_id(
            user.id
        ):
            raise ConflictError(
                "A provider profile already exists for this user."
            )

        provider = await self.providers.create(
            user.id,
            data,
        )

        await self.db.commit()
        await self.db.refresh(provider)

        return provider

    async def get_my_profile(
        self,
        user: User,
    ) -> Provider:
        provider = await self.providers.get_by_user_id(
            user.id
        )

        if provider is None:
            raise NotFoundError(
                "Provider profile not found."
            )

        return provider

    async def update_my_profile(
        self,
        user: User,
        data: ProviderProfileUpdate,
    ) -> Provider:
        if not data.model_fields_set:
            raise BadRequestError(
                "At least one provider field is required."
            )

        provider = await self.get_my_profile(user)

        provider = await self.providers.update_profile(
            provider,
            data,
        )

        await self.db.commit()
        await self.db.refresh(provider)

        return provider

    async def list_portfolio(
        self,
        user: User,
    ):
        provider = await self.get_my_profile(user)

        return await self.providers.list_portfolio_images(
            provider.id
        )

    async def add_portfolio_image(
        self,
        user: User,
        data: PortfolioImageCreate,
    ):
        provider = await self.get_my_profile(user)

        image = await self.providers.add_portfolio_image(
            provider.id,
            data,
        )

        await self.db.commit()
        await self.db.refresh(image)

        return image

    async def delete_portfolio_image(
        self,
        user: User,
        image_id: int,
    ) -> None:
        provider = await self.get_my_profile(user)

        image = await self.providers.get_portfolio_image(
            provider.id,
            image_id,
        )

        if image is None:
            raise NotFoundError(
                "Portfolio image not found."
            )

        await self.providers.delete_portfolio_image(
            image
        )

        await self.db.commit()

    async def statistics(
        self,
        user: User,
    ) -> ProviderStatisticsRead:
        provider = await self.get_my_profile(user)

        values = await self.providers.statistics(
            provider.id
        )

        return ProviderStatisticsRead(
            provider_id=provider.id,
            average_rating=provider.rating,
            **values,
        )