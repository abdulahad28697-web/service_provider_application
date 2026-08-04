"""HTTP endpoints for provider profiles and portfolios."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import StandardResponse, success_response
from app.core.dependencies import get_current_user
from app.core.permissions import require_provider
from app.database.session import get_db
from app.models.user import User
from app.schemas.admin import ProviderOnboard, ProviderRead
from app.schemas.provider import (
    PortfolioImageCreate,
    PortfolioImageRead,
    ProviderProfileUpdate,
    ProviderStatisticsRead,
)
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/providers", tags=["Providers"])


def _service(
    db: AsyncSession = Depends(get_db),
) -> ProviderService:
    """Create a provider service for the current request."""
    return ProviderService(db)


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
    provider = await service.apply(user, payload)

    return success_response(
        data=ProviderRead.model_validate(provider),
        message="Provider application submitted for verification.",
    )


@router.get(
    "/me",
    response_model=StandardResponse,
    summary="Get my provider profile",
)
async def get_my_provider_profile(
    service: ProviderService = Depends(_service),
    user: User = Depends(require_provider),
):
    provider = await service.get_my_profile(user)

    return success_response(
        data=ProviderRead.model_validate(provider),
        message="Provider profile fetched.",
    )


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
    provider = await service.update_my_profile(user, payload)

    return success_response(
        data=ProviderRead.model_validate(provider),
        message="Provider profile updated.",
    )


@router.get(
    "/me/portfolio",
    response_model=StandardResponse,
    summary="List my portfolio images",
)
async def list_my_portfolio(
    service: ProviderService = Depends(_service),
    user: User = Depends(require_provider),
):
    images = await service.list_portfolio(user)

    return success_response(
        data=[
            PortfolioImageRead.model_validate(image)
            for image in images
        ],
        message="Portfolio fetched.",
    )


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
    image = await service.add_portfolio_image(user, payload)

    return success_response(
        data=PortfolioImageRead.model_validate(image),
        message="Portfolio image added.",
    )


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
    await service.delete_portfolio_image(user, image_id)

    return success_response(
        data=None,
        message="Portfolio image deleted.",
    )


@router.get(
    "/me/statistics",
    response_model=StandardResponse,
    summary="View my provider statistics",
)
async def provider_statistics(
    service: ProviderService = Depends(_service),
    user: User = Depends(require_provider),
):
    statistics = await service.get_statistics(user)

    return success_response(
        data=ProviderStatisticsRead.model_validate(statistics),
        message="Provider statistics fetched.",
    )