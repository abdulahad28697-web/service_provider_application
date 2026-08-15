"""HTTP endpoints for user profile management."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import StandardResponse, success_response
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.user_profile import (
    AddressCreate,
    AddressRead,
    AddressUpdate,
    DeleteAccountRequest,
    FavoriteServiceRead,
    UserProfileUpdate,
)
from app.services.user_profile_service import UserProfileService


router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


def _service(
    db: AsyncSession = Depends(get_db),
) -> UserProfileService:
    """Create a user-profile service for the current request."""
    return UserProfileService(db)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=StandardResponse,
    summary="View my profile",
)
async def view_profile(
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    profile = await service.get_profile(user)

    return success_response(
        data=profile,
        message="Profile fetched.",
    )


@router.patch(
    "/me",
    response_model=StandardResponse,
    summary="Update my profile",
)
async def update_profile(
    payload: UserProfileUpdate,
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    profile = await service.update_profile(
        user,
        payload,
    )

    return success_response(
        data=profile,
        message="Profile updated.",
    )


@router.delete(
    "/me",
    response_model=StandardResponse,
    summary="Deactivate my account",
)
async def delete_account(
    payload: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    await service.delete_account(
        user,
        payload,
    )

    return success_response(
        data=None,
        message="Account deactivated successfully.",
    )


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------

@router.get(
    "/me/addresses",
    response_model=StandardResponse,
    summary="List my addresses",
)
async def list_addresses(
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    addresses = await service.list_addresses(user)

    return success_response(
        data=[
            AddressRead.model_validate(address)
            for address in addresses
        ],
        message="Addresses fetched.",
    )


@router.post(
    "/me/addresses",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an address",
)
async def create_address(
    payload: AddressCreate,
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    address = await service.create_address(
        user,
        payload,
    )

    return success_response(
        data=AddressRead.model_validate(address),
        message="Address created.",
    )


@router.patch(
    "/me/addresses/{address_id}",
    response_model=StandardResponse,
    summary="Update an address",
)
async def update_address(
    address_id: int,
    payload: AddressUpdate,
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    address = await service.update_address(
        user,
        address_id,
        payload,
    )

    return success_response(
        data=AddressRead.model_validate(address),
        message="Address updated.",
    )


@router.delete(
    "/me/addresses/{address_id}",
    response_model=StandardResponse,
    summary="Delete an address",
)
async def delete_address(
    address_id: int,
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    await service.delete_address(
        user,
        address_id,
    )

    return success_response(
        data=None,
        message="Address deleted.",
    )


# ---------------------------------------------------------------------------
# Favorite services
# ---------------------------------------------------------------------------

@router.get(
    "/me/favorites",
    response_model=StandardResponse,
    summary="List favorite services",
)
async def list_favorites(
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    favorites = await service.list_favorites(user)

    return success_response(
        data=[
            FavoriteServiceRead.model_validate(favorite)
            for favorite in favorites
        ],
        message="Favorite services fetched.",
    )


@router.post(
    "/me/favorites/{service_id}",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a service to favorites",
)
async def add_favorite(
    service_id: int,
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    favorite = await service.add_favorite(
        user,
        service_id,
    )

    return success_response(
        data=FavoriteServiceRead.model_validate(favorite),
        message="Service added to favorites.",
    )


@router.delete(
    "/me/favorites/{service_id}",
    response_model=StandardResponse,
    summary="Remove a service from favorites",
)
async def remove_favorite(
    service_id: int,
    user: User = Depends(get_current_user),
    service: UserProfileService = Depends(_service),
):
    await service.remove_favorite(
        user,
        service_id,
    )

    return success_response(
        data=None,
        message="Service removed from favorites.",
    )