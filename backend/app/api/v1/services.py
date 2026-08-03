"""HTTP endpoints for services, including search and filtering."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PageParams
from app.common.responses import MessageResponse, StandardResponse, success_response
from app.core.permissions import get_provider_profile, require_provider
from app.database.session import get_db
from app.models.user import User
from app.repositories.service_filters import ServiceFilters
from app.schemas.service import ServiceCreate, ServicePage, ServiceRead, ServiceUpdate
from app.services.service_service import ServiceService

router = APIRouter(prefix="/services", tags=["Services"])


def _service(db: AsyncSession = Depends(get_db)) -> ServiceService:
    """Build a :class:`ServiceService` bound to the request session."""
    return ServiceService(db)


def _filters(
    category_id: Optional[int] = Query(default=None),
    provider_id: Optional[int] = Query(default=None),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    is_active: Optional[bool] = Query(default=None),
    is_featured: Optional[bool] = Query(default=None),
    q: Optional[str] = Query(default=None, description="Search text."),
    sort_by: str = Query(default="newest"),
    sort_dir: str = Query(default="desc"),
) -> ServiceFilters:
    """Assemble the service query filters from request query parameters."""
    return ServiceFilters(
        category_id=category_id,
        provider_id=provider_id,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
        is_featured=is_featured,
        query=q,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.post(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a service",
)
async def create_service(
    payload: ServiceCreate,
    service: ServiceService = Depends(_service),
    user: User = Depends(require_provider),
    db: AsyncSession = Depends(get_db),
):
    provider = await get_provider_profile(db, user)
    created = await service.create(payload, provider)
    return success_response(
        data=ServiceRead.model_validate(created), message="Service created."
    )


@router.get(
    "",
    response_model=StandardResponse,
    summary="List / search / filter services",
)
async def list_services(
    params: PageParams = Depends(),
    filters: ServiceFilters = Depends(_filters),
    service: ServiceService = Depends(_service),
):
    page = await service.list(params, filters)
    return success_response(
        data=ServicePage.model_validate(page), message="Services fetched."
    )


@router.get(
    "/{service_id}",
    response_model=StandardResponse,
    summary="Get a service by id",
)
async def get_service(
    service_id: int,
    service: ServiceService = Depends(_service),
):
    read = await service.get_read(service_id)
    return success_response(data=read, message="Service fetched.")


@router.patch(
    "/{service_id}",
    response_model=StandardResponse,
    summary="Update a service (owner)",
)
async def update_service(
    service_id: int,
    payload: ServiceUpdate,
    service: ServiceService = Depends(_service),
    user: User = Depends(require_provider),
):
    updated = await service.update(service_id, payload, user)
    return success_response(
        data=ServiceRead.model_validate(updated), message="Service updated."
    )


@router.delete(
    "/{service_id}",
    response_model=MessageResponse,
    summary="Delete a service (owner)",
)
async def delete_service(
    service_id: int,
    service: ServiceService = Depends(_service),
    user: User = Depends(require_provider),
):
    await service.delete(service_id, user)
    return MessageResponse(message="Service deleted.", data=None)
