"""Data-access operations for profiles, addresses, and favorites."""

from typing import Optional, Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.models.user_profile import (
    FavoriteService,
    UserAddress,
    UserProfile,
)
from app.schemas.user_profile import (
    AddressCreate,
    AddressUpdate,
)


class UserProfileRepository:
    """Async persistence operations for user-management data."""

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    async def get_profile(
        self,
        user_id: int,
    ) -> Optional[UserProfile]:
        result = await self.db.execute(
            select(UserProfile).where(
                UserProfile.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    async def get_or_create_profile(
        self,
        user_id: int,
    ) -> UserProfile:
        profile = await self.get_profile(user_id)

        if profile:
            return profile

        profile = UserProfile(
            user_id=user_id
        )

        self.db.add(profile)
        await self.db.flush()

        return profile

    async def list_addresses(
        self,
        user_id: int,
    ) -> Sequence[UserAddress]:
        result = await self.db.execute(
            select(UserAddress)
            .where(
                UserAddress.user_id == user_id
            )
            .order_by(
                UserAddress.is_default.desc(),
                UserAddress.created_at.desc(),
            )
        )

        return result.scalars().all()

    async def get_address(
        self,
        user_id: int,
        address_id: int,
    ) -> Optional[UserAddress]:
        result = await self.db.execute(
            select(UserAddress).where(
                UserAddress.id == address_id,
                UserAddress.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def clear_default_addresses(
        self,
        user_id: int,
    ) -> None:
        await self.db.execute(
            update(UserAddress)
            .where(
                UserAddress.user_id == user_id
            )
            .values(is_default=False)
        )

    async def create_address(
        self,
        user_id: int,
        data: AddressCreate,
    ) -> UserAddress:
        count = await self.db.scalar(
            select(
                func.count(UserAddress.id)
            ).where(
                UserAddress.user_id == user_id
            )
        )

        address_data = data.model_dump()

        if not count:
            address_data["is_default"] = True

        if address_data["is_default"]:
            await self.clear_default_addresses(
                user_id
            )

        address = UserAddress(
            user_id=user_id,
            **address_data,
        )

        self.db.add(address)
        await self.db.flush()

        return address

    async def update_address(
        self,
        address: UserAddress,
        data: AddressUpdate,
    ) -> UserAddress:
        update_data = data.model_dump(
            exclude_unset=True
        )

        if update_data.get("is_default") is True:
            await self.clear_default_addresses(
                address.user_id
            )

        for field, value in update_data.items():
            setattr(address, field, value)

        self.db.add(address)
        await self.db.flush()

        return address

    async def delete_address(
        self,
        address: UserAddress,
    ) -> None:
        user_id = address.user_id
        was_default = address.is_default

        await self.db.delete(address)
        await self.db.flush()

        if was_default:
            result = await self.db.execute(
                select(UserAddress)
                .where(
                    UserAddress.user_id == user_id
                )
                .order_by(
                    UserAddress.created_at.asc()
                )
                .limit(1)
            )

            next_address = (
                result.scalar_one_or_none()
            )

            if next_address:
                next_address.is_default = True
                self.db.add(next_address)
                await self.db.flush()

    async def get_favorite(
        self,
        user_id: int,
        service_id: int,
    ) -> Optional[FavoriteService]:
        result = await self.db.execute(
            select(FavoriteService).where(
                FavoriteService.user_id == user_id,
                FavoriteService.service_id
                == service_id,
            )
        )

        return result.scalar_one_or_none()

    async def add_favorite(
        self,
        user_id: int,
        service_id: int,
    ) -> FavoriteService:
        favorite = FavoriteService(
            user_id=user_id,
            service_id=service_id,
        )

        self.db.add(favorite)
        await self.db.flush()

        return favorite

    async def list_favorites(
        self,
        user_id: int,
    ):
        result = await self.db.execute(
            select(
                FavoriteService,
                Service,
            )
            .join(
                Service,
                Service.id
                == FavoriteService.service_id,
            )
            .where(
                FavoriteService.user_id == user_id
            )
            .order_by(
                FavoriteService.created_at.desc()
            )
        )

        return result.all()

    async def remove_favorite(
        self,
        favorite: FavoriteService,
    ) -> None:
        await self.db.delete(favorite)
        await self.db.flush()