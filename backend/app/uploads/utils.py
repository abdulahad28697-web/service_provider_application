"""Validation and path utilities for uploaded images."""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.exceptions import BadRequestError

MEDIA_ROOT = Path("media")
PROFILE_PICTURES_DIR = MEDIA_ROOT / "profile_pictures"
PROVIDER_PORTFOLIOS_DIR = MEDIA_ROOT / "provider_portfolios"
SERVICES_DIR = MEDIA_ROOT / "services"

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def ensure_upload_directories() -> None:
    """Create upload directories if they do not exist."""
    PROFILE_PICTURES_DIR.mkdir(parents=True, exist_ok=True)
    PROVIDER_PORTFOLIOS_DIR.mkdir(parents=True, exist_ok=True)
    SERVICES_DIR.mkdir(parents=True, exist_ok=True)


def validate_image_type(file: UploadFile) -> str:
    """Validate the uploaded image MIME type and return its extension."""
    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")

    if extension is None:
        raise BadRequestError(
            "Only JPG, PNG and WEBP image files are allowed."
        )

    return extension


def generate_unique_filename(extension: str) -> str:
    """Generate a safe random filename."""
    return f"{uuid4().hex}{extension}"


def media_url(directory: str, filename: str) -> str:
    """Build the public URL for an uploaded media file."""
    return f"/media/{directory}/{filename}"