"""HTTP endpoints for provider profiles, portfolios and public availability."""

from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import (
    StandardResponse,
    success_response,
)
from app.core.dependencies import get_current_user
from app.core.permissions import require_provider
from app.database.session import get_db
from app.models.user import User

from app.schemas.admin import (
    ProviderOnboard,
    ProviderRead,
)

from app.schemas.provider import (
    PortfolioImageCreate,
    PortfolioImageRead,
    ProviderProfileUpdate,
    ProviderPublicRead,
    ProviderStatisticsRead,
)

from app.schemas.schedule import ScheduleSlotRead

from app.services.provider_service import ProviderService


router = APIRouter(
    prefix="/providers",
    tags=["Providers"],
)


def _service(
    db: AsyncSession = Depends(get_db),
) -> ProviderService:
    """Create a provider service for the current request."""

    return ProviderService(db)


# ============================================================
# APPLY TO BECOME PROVIDER
# ============================================================


@router.post(
    "/become",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to become a provider",
)
async def become_provider(
    payload: ProviderOnboard,
    service: ProviderService = Depends(_service),
    user: User = Depends(get_current_user),
):
    provider = await service.apply(
        user,
        payload,
    )

    return success_response(
        data=ProviderRead.model_validate(
            provider
        ),
        message=(
            "Provider application submitted "
            "for verification."
        ),
    )


# ============================================================
# MY PROVIDER PROFILE
# ============================================================


@router.get(
    "/me",
    response_model=StandardResponse,
    summary="Get my provider profile",
)
async def get_my_provider_profile(
    service: ProviderService = Depends(_service),
    user: User = Depends(get_current_user),
):
    provider = await service.get_my_profile(
        user
    )

    return success_response(
        data=ProviderRead.model_validate(
            provider
        ),
        message="Provider profile fetched.",
    )


# ============================================================
# UPDATE MY PROVIDER PROFILE
# ============================================================


@router.patch(
    "/me",
    response_model=StandardResponse,
    summary="Update my provider profile",
)
async def update_my_provider_profile(
    payload: ProviderProfileUpdate,
    service: ProviderService = Depends(_service),
    user: User = Depends(require_provider),
):
    provider = await service.update_my_profile(
        user,
        payload,
    )

    return success_response(
        data=ProviderRead.model_validate(
            provider
        ),
        message="Provider profile updated.",
    )


# ============================================================
# MY PORTFOLIO
# ============================================================


@router.get(
    "/me/portfolio",
    response_model=StandardResponse,
    summary="List my portfolio images",
)
async def list_my_portfolio(
    service: ProviderService = Depends(_service),
    user: User = Depends(require_provider),
):
    images = await service.list_portfolio(
        user
    )

    return success_response(
        data=[
            PortfolioImageRead.model_validate(
                image
            )
            for image in images
        ],
        message="Portfolio fetched.",
    )


# ============================================================
# ADD PORTFOLIO IMAGE
# ============================================================


@router.post(
    "/me/portfolio",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a portfolio image",
)
async def add_portfolio_image(
    payload: PortfolioImageCreate,
    service: ProviderService = Depends(_service),
    user: User = Depends(require_provider),
):
    image = await service.add_portfolio_image(
        user,
        payload,
    )

    return success_response(
        data=PortfolioImageRead.model_validate(
            image
        ),
        message="Portfolio image added.",
    )


# ============================================================
# DELETE PORTFOLIO IMAGE
# ============================================================


@router.delete(
    "/me/portfolio/{image_id}",
    response_model=StandardResponse,
    summary="Delete a portfolio image",
)
async def delete_portfolio_image(
    image_id: int,
    service: ProviderService = Depends(_service),
    user: User = Depends(require_provider),
):
    await service.delete_portfolio_image(
        user,
        image_id,
    )

    return success_response(
        data=None,
        message="Portfolio image deleted.",
    )


# ============================================================
# MY PROVIDER STATISTICS
# ============================================================


@router.get(
    "/me/statistics",
    response_model=StandardResponse,
    summary="View my provider statistics",
)
async def provider_statistics(
    service: ProviderService = Depends(_service),
    user: User = Depends(require_provider),
):
    statistics = await service.statistics(
        user
    )

    return success_response(
        data=ProviderStatisticsRead.model_validate(
            statistics
        ),
        message="Provider statistics fetched.",
    )


# ============================================================
# PUBLIC PROVIDER AVAILABILITY
#
# This route must stay before /{provider_id}
# ============================================================


@router.get(
    "/{provider_id}/availability",
    response_model=StandardResponse,
    summary="View provider weekly availability",
)
async def get_public_provider_availability(
    provider_id: int,
    service: ProviderService = Depends(_service),
):
    availability = await service.public_availability(
        provider_id
    )

    return success_response(
        data=[
            ScheduleSlotRead.model_validate(
                slot
            )
            for slot in availability
        ],
        message="Provider availability fetched.",
    )


# ============================================================
# REAL AVAILABLE BOOKING SLOTS
#
# Example:
# /providers/2/available-slots?service_id=3&date=2026-08-15
#
# This considers:
# - provider weekly schedule
# - service duration
# - pending bookings
# - accepted bookings
# ============================================================


@router.get(
    "/{provider_id}/available-slots",
    response_model=StandardResponse,
    summary="Get conflict-free provider booking slots",
)
async def get_provider_available_slots(
    provider_id: int,

    service_id: int = Query(
        ...,
        gt=0,
        description="Service to calculate available slots for.",
    ),

    date_value: date = Query(
        ...,
        alias="date",
        description="Booking date in YYYY-MM-DD format.",
    ),

    service: ProviderService = Depends(_service),
):
    slots = await service.available_slots(
        provider_id=provider_id,
        service_id=service_id,
        selected_date=date_value,
    )

    return success_response(
        data={
            "provider_id": provider_id,
            "service_id": service_id,
            "date": date_value.isoformat(),
            "slots": slots,
        },
        message="Available booking slots fetched.",
    )


# ============================================================
# PUBLIC PROVIDER PROFILE
#
# IMPORTANT:
# Keep this route LAST because /{provider_id} is dynamic.
# ============================================================


@router.get(
    "/{provider_id}",
    response_model=StandardResponse,
    summary="View a provider public profile",
)
async def get_public_provider_profile(
    provider_id: int,
    service: ProviderService = Depends(_service),
):
    profile = await service.get_public_profile(
        provider_id
    )

    return success_response(
        data=ProviderPublicRead.model_validate(
            profile
        ),
        message="Provider public profile fetched.",
    )