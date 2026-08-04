"""Business logic for user profiles, addresses, and favorites."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)
from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_profile_repository import (
    UserProfileRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user_profile import (
    AddressCreate,
    AddressUpdate,
    DeleteAccountRequest,
    FavoriteProviderRead,
    UserProfileRead,
    UserProfileUpdate,
)


class UserProfileService:
    """User-management business rules."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.profiles = UserProfileRepository(db)

    def _profile_response(
        self,
        user: User,
        profile,
    ) -> UserProfileRead:
        return UserProfileRead(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            phone_number=profile.phone_number,
            bio=profile.bio,
            profile_picture_url=(
                profile.profile_picture_url
            ),
            created_at=user.created_at,
            updated_at=profile.updated_at,
        )

    async def get_profile(
        self,
        user: User,
    ) -> UserProfileRead:
        profile = (
            await self.profiles.get_or_create_profile(
                user.id
            )
        )

        await self.db.commit()
        await self.db.refresh(profile)

        return self._profile_response(
            user,
            profile,
        )

    async def update_profile(
        self,
        user: User,
        data: UserProfileUpdate,
    ) -> UserProfileRead:
        if not data.model_fields_set:
            raise BadRequestError(
                "At least one profile field is required."
            )

        if data.email:
            normalized_email = (
                str(data.email).strip().lower()
            )

            if normalized_email != user.email:
                existing_user = (
                    await self.users.get_by_email(
                        normalized_email
                    )
                )

                if existing_user:
                    raise ConflictError(
                        "A user with this email already exists."
                    )

                user.email = normalized_email

        if data.full_name is not None:
            cleaned_name = " ".join(
                data.full_name.split()
            )

            if not cleaned_name:
                raise BadRequestError(
                    "Full name cannot be empty."
                )

            user.full_name = cleaned_name

        profile = (
            await self.profiles.get_or_create_profile(
                user.id
            )
        )

        if "phone_number" in data.model_fields_set:
            profile.phone_number = data.phone_number

        if "bio" in data.model_fields_set:
            profile.bio = data.bio

        self.db.add(user)
        self.db.add(profile)

        await self.db.commit()
        await self.db.refresh(user)
        await self.db.refresh(profile)

        return self._profile_response(
            user,
            profile,
        )

    async def delete_account(
        self,
        user: User,
        data: DeleteAccountRequest,
    ) -> None:
        if not verify_password(
            data.password,
            user.hashed_password,
        ):
            raise BadRequestError(
                "Password is incorrect."
            )

        user.is_active = False
        self.db.add(user)

        await self.db.commit()

    async def list_addresses(
        self,
        user: User,
    ):
        return await self.profiles.list_addresses(
            user.id
        )

    async def create_address(
        self,
        user: User,
        data: AddressCreate,
    ):
        address = await self.profiles.create_address(
            user.id,
            data,
        )

        await self.db.commit()
        await self.db.refresh(address)

        return address

    async def update_address(
        self,
        user: User,
        address_id: int,
        data: AddressUpdate,
    ):
        if not data.model_fields_set:
            raise BadRequestError(
                "At least one address field is required."
            )

        address = await self.profiles.get_address(
            user.id,
            address_id,
        )

        if address is None:
            raise NotFoundError(
                "Address not found."
            )

        address = await self.profiles.update_address(
            address,
            data,
        )

        await self.db.commit()
        await self.db.refresh(address)

        return address

    async def delete_address(
        self,
        user: User,
        address_id: int,
    ) -> None:
        address = await self.profiles.get_address(
            user.id,
            address_id,
        )

        if address is None:
            raise NotFoundError(
                "Address not found."
            )

        await self.profiles.delete_address(
            address
        )

        await self.db.commit()

    async def list_favorites(
        self,
        user: User,
    ) -> list[FavoriteProviderRead]:
        rows = await self.profiles.list_favorites(
            user.id
        )

        return [
            FavoriteProviderRead(
                id=favorite.id,
                provider_id=provider.id,
                business_name=provider.business_name,
                category=provider.category,
                city=provider.city,
                rating=float(provider.rating),
                hourly_rate=float(
                    provider.hourly_rate
                ),
                created_at=favorite.created_at,
            )
            for favorite, provider in rows
        ]

    async def add_favorite(
        self,
        user: User,
        provider_id: int,
    ) -> FavoriteProviderRead:
        provider = await self.profiles.get_provider(
            provider_id
        )

        if provider is None or not provider.is_verified:
            raise NotFoundError(
                "Provider not found."
            )

        existing = await self.profiles.get_favorite(
            user.id,
            provider_id,
        )

        if existing:
            raise ConflictError(
                "Provider is already in favorites."
            )

        favorite = await self.profiles.add_favorite(
            user.id,
            provider_id,
        )

        await self.db.commit()
        await self.db.refresh(favorite)

        return FavoriteProviderRead(
            id=favorite.id,
            provider_id=provider.id,
            business_name=provider.business_name,
            category=provider.category,
            city=provider.city,
            rating=float(provider.rating),
            hourly_rate=float(provider.hourly_rate),
            created_at=favorite.created_at,
        )

    async def remove_favorite(
        self,
        user: User,
        provider_id: int,
    ) -> None:
        favorite = await self.profiles.get_favorite(
            user.id,
            provider_id,
        )

        if favorite is None:
            raise NotFoundError(
                "Favorite provider not found."
            )

        await self.profiles.remove_favorite(
            favorite
        )

        await self.db.commit()