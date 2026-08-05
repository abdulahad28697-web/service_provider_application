"""HTTP endpoints for user and provider image uploads."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.common.responses import StandardResponse, success_response
from app.core.dependencies import get_current_user
from app.core.permissions import require_provider
from app.models.user import User
from app.uploads.service import UploadService

router = APIRouter(prefix="/uploads", tags=["File Uploads"])


def _service() -> UploadService:
    """Create the upload service."""
    return UploadService()


@router.post(
    "/profile-picture",
    response_model=StandardResponse,
    summary="Upload a user profile picture",
)
async def upload_profile_picture(
    file: UploadFile = File(...),
    service: UploadService = Depends(_service),
    _user: User = Depends(get_current_user),
):
    image_url = await service.save_image(
        file,
        category="profile_pictures",
    )

    return success_response(
        data={"image_url": image_url},
        message="Profile picture uploaded.",
    )


@router.post(
    "/provider-portfolio",
    response_model=StandardResponse,
    summary="Upload a provider portfolio image",
)
async def upload_provider_portfolio_image(
    file: UploadFile = File(...),
    service: UploadService = Depends(_service),
    _provider: User = Depends(require_provider),
):
    image_url = await service.save_image(
        file,
        category="provider_portfolios",
    )

    return success_response(
        data={"image_url": image_url},
        message="Portfolio image uploaded.",
    )