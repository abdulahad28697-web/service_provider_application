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
from app.repositories.user_repository import (
    UserRepository,
)
from app.schemas.user_profile import (
    AddressCreate,
    AddressUpdate,
    DeleteAccountRequest,
    FavoriteServiceRead,
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

    # ========================================================
    # PROFILE RESPONSE
    # ========================================================

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

    # ========================================================
    # GET PROFILE
    # ========================================================

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

    # ========================================================
    # UPDATE PROFILE
    # ========================================================

    async def update_profile(
        self,
        user: User,
        data: UserProfileUpdate,
    ) -> UserProfileRead:
        if not data.model_fields_set:
            raise BadRequestError(
                "At least one profile field is required."
            )

        # ----------------------------------------------------
        # EMAIL
        # ----------------------------------------------------

        if "email" in data.model_fields_set:
            if data.email is None:
                raise BadRequestError(
                    "Email cannot be empty."
                )

            normalized_email = (
                str(data.email)
                .strip()
                .lower()
            )

            if normalized_email != user.email:
                existing_user = (
                    await self.users.get_by_email(
                        normalized_email
                    )
                )

                if (
                    existing_user
                    and existing_user.id != user.id
                ):
                    raise ConflictError(
                        "A user with this email already exists."
                    )

                user.email = normalized_email

        # ----------------------------------------------------
        # FULL NAME
        # ----------------------------------------------------

        if "full_name" in data.model_fields_set:
            if data.full_name is None:
                raise BadRequestError(
                    "Full name cannot be empty."
                )

            cleaned_name = " ".join(
                data.full_name.split()
            )

            if not cleaned_name:
                raise BadRequestError(
                    "Full name cannot be empty."
                )

            user.full_name = cleaned_name

        # ----------------------------------------------------
        # GET / CREATE PROFILE RECORD
        # ----------------------------------------------------

        profile = (
            await self.profiles.get_or_create_profile(
                user.id
            )
        )

        # ----------------------------------------------------
        # PHONE NUMBER
        # ----------------------------------------------------

        if "phone_number" in data.model_fields_set:
            profile.phone_number = (
                data.phone_number.strip()
                if data.phone_number
                else None
            )

        # ----------------------------------------------------
        # BIO
        # ----------------------------------------------------

        if "bio" in data.model_fields_set:
            profile.bio = (
                data.bio.strip()
                if data.bio
                else None
            )

        # ----------------------------------------------------
        # PROFILE PICTURE
        # ----------------------------------------------------

        if (
            "profile_picture_url"
            in data.model_fields_set
        ):
            profile.profile_picture_url = (
                data.profile_picture_url.strip()
                if data.profile_picture_url
                else None
            )

        self.db.add(user)
        self.db.add(profile)

        await self.db.commit()

        await self.db.refresh(user)
        await self.db.refresh(profile)

        return self._profile_response(
            user,
            profile,
        )

    # ========================================================
    # DELETE / DEACTIVATE ACCOUNT
    # ========================================================

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

    # ========================================================
    # ADDRESSES
    # ========================================================

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
        address = (
            await self.profiles.create_address(
                user.id,
                data,
            )
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

        address = (
            await self.profiles.get_address(
                user.id,
                address_id,
            )
        )

        if address is None:
            raise NotFoundError(
                "Address not found."
            )

        address = (
            await self.profiles.update_address(
                address,
                data,
            )
        )

        await self.db.commit()
        await self.db.refresh(address)

        return address

    async def delete_address(
        self,
        user: User,
        address_id: int,
    ) -> None:
        address = (
            await self.profiles.get_address(
                user.id,
                address_id,
            )
        )

        if address is None:
            raise NotFoundError(
                "Address not found."
            )

        await self.profiles.delete_address(
            address
        )

        await self.db.commit()

    # ========================================================
    # FAVORITES
    # ========================================================

    async def _hydrate_favorite(self, favorite, service) -> FavoriteServiceRead:
        from app.models.category import Category
        from app.models.provider import Provider
        from app.models.user import User
        from app.models.review import Review
        from app.models.booking import Booking
        from sqlalchemy import func, select

        # Category Name
        category_name = None
        category_result = await self.db.execute(
            select(Category.name).where(Category.id == service.category_id)
        )
        category_name = category_result.scalar_one_or_none()

        # Provider details
        provider_name = None
        provider_rating = 0.0
        provider_result = await self.db.execute(
            select(
                User.full_name,
                Provider.rating,
                Provider.business_name,
            )
            .join(
                Provider,
                Provider.user_id == User.id,
            )
            .where(
                Provider.id == service.provider_id
            )
        )
        provider_row = provider_result.first()
        if provider_row is not None:
            provider_name = provider_row[2] or provider_row[0]
            provider_rating = float(provider_row[1] or 0)

        # Review count
        review_count_result = await self.db.execute(
            select(func.count(Review.id))
            .join(
                Booking,
                Review.booking_id == Booking.id,
            )
            .where(
                Booking.provider_id == service.provider_id
            )
        )
        review_count = review_count_result.scalar_one() or 0

        return FavoriteServiceRead(
            id=favorite.id,
            service_id=service.id,
            title=service.title,
            price=float(service.price or 0),
            price_unit=service.price_unit.value,
            duration_minutes=service.duration_minutes,
            images=service.images or [],
            category_name=category_name,
            provider_name=provider_name,
            provider_rating=provider_rating,
            review_count=review_count,
            created_at=favorite.created_at,
        )

    async def list_favorites(
        self,
        user: User,
    ) -> list[FavoriteServiceRead]:
        rows = (
            await self.profiles.list_favorites(
                user.id
            )
        )

        return [
            await self._hydrate_favorite(favorite, service)
            for favorite, service in rows
        ]

    async def add_favorite(
        self,
        user: User,
        service_id: int,
    ) -> FavoriteServiceRead:
        from app.models.service import Service
        service = await self.db.get(Service, service_id)

        if service is None:
            raise NotFoundError(
                "Service not found."
            )

        existing = (
            await self.profiles.get_favorite(
                user.id,
                service_id,
            )
        )

        if existing:
            raise ConflictError(
                "Service is already in favorites."
            )

        favorite = (
            await self.profiles.add_favorite(
                user.id,
                service_id,
            )
        )

        await self.db.commit()
        await self.db.refresh(favorite)

        return await self._hydrate_favorite(favorite, service)

    async def remove_favorite(
        self,
        user: User,
        service_id: int,
    ) -> None:
        favorite = (
            await self.profiles.get_favorite(
                user.id,
                service_id,
            )
        )

        if favorite is None:
            raise NotFoundError(
                "Favorite service not found."
            )

        await self.profiles.remove_favorite(
            favorite
        )

        await self.db.commit()