"""Business logic for secure image uploads."""

from pathlib import Path
from typing import Literal, Optional

from fastapi import UploadFile

from app.core.exceptions import BadRequestError
from app.uploads.utils import (
    MAX_FILE_SIZE,
    PROFILE_PICTURES_DIR,
    PROVIDER_PORTFOLIOS_DIR,
    SERVICES_DIR,
    ensure_upload_directories,
    generate_unique_filename,
    media_url,
    validate_image_type,
)

UploadCategory = Literal["profile_pictures", "provider_portfolios", "services"]


class UploadService:
    """Validate, save and remove uploaded images."""

    def __init__(self) -> None:
        ensure_upload_directories()

    def _directory(self, category: UploadCategory) -> Path:
        """Return the storage directory for an upload category."""
        if category == "profile_pictures":
            return PROFILE_PICTURES_DIR

        if category == "provider_portfolios":
            return PROVIDER_PORTFOLIOS_DIR

        if category == "services":
            return SERVICES_DIR

        raise BadRequestError("Invalid upload category.")

    async def save_image(
        self,
        file: UploadFile,
        category: UploadCategory,
    ) -> str:
        """Validate and save an image, returning its public URL."""
        extension = validate_image_type(file)

        content = await file.read(MAX_FILE_SIZE + 1)
        await file.close()

        if not content:
            raise BadRequestError("The uploaded file is empty.")

        if len(content) > MAX_FILE_SIZE:
            raise BadRequestError(
                "Image size must not exceed 5 MB."
            )

        filename = generate_unique_filename(extension)
        destination = self._directory(category) / filename

        try:
            destination.write_bytes(content)
        except OSError as exc:
            raise BadRequestError(
                "The image could not be saved."
            ) from exc

        return media_url(category, filename)

    def delete_image(
        self,
        image_url: Optional[str],
    ) -> None:
        """Delete a locally stored media file if it exists."""
        if not image_url or not image_url.startswith("/media/"):
            return

        relative_path = image_url.removeprefix("/media/")
        candidate = (Path("media") / relative_path).resolve()
        media_root = Path("media").resolve()

        if media_root not in candidate.parents:
            raise BadRequestError("Invalid media file path.")

        if candidate.is_file():
            candidate.unlink()