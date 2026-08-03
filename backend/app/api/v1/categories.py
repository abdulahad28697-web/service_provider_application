"""HTTP endpoints for categories."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PageParams
from app.common.responses import MessageResponse, StandardResponse, success_response
from app.core.permissions import require_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryPage,
    CategoryRead,
    CategoryUpdate,
)
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


def _service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    """Build a :class:`CategoryService` bound to the request session."""
    return CategoryService(db)


@router.post(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
)
async def create_category(
    payload: CategoryCreate,
    service: CategoryService = Depends(_service),
    _admin: User = Depends(require_admin),
):
    category = await service.create(payload)
    return success_response(
        data=CategoryRead.model_validate(category),
        message="Category created.",
    )


@router.get(
    "",
    response_model=StandardResponse,
    summary="List categories",
)
async def list_categories(
    params: PageParams = Depends(),
    include_inactive: bool = Query(
        default=False, description="Include deactivated categories (admin use)."
    ),
    service: CategoryService = Depends(_service),
):
    page = await service.list(params, include_inactive=include_inactive)
    return success_response(
        data=CategoryPage.model_validate(page), message="Categories fetched."
    )


@router.get(
    "/{category_id}",
    response_model=StandardResponse,
    summary="Get a category by id",
)
async def get_category(
    category_id: int,
    service: CategoryService = Depends(_service),
):
    category = await service.get(category_id)
    return success_response(
        data=CategoryRead.model_validate(category),
        message="Category fetched.",
    )


@router.patch(
    "/{category_id}",
    response_model=StandardResponse,
    summary="Update a category",
)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    service: CategoryService = Depends(_service),
    _admin: User = Depends(require_admin),
):
    category = await service.update(category_id, payload)
    return success_response(
        data=CategoryRead.model_validate(category),
        message="Category updated.",
    )


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    summary="Delete a category",
)
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(_service),
    _admin: User = Depends(require_admin),
):
    await service.delete(category_id)
    return MessageResponse(message="Category deleted.", data=None)
