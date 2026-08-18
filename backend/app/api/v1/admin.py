"""HTTP endpoints for admin operations and provider onboarding."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.pagination import PageParams
from app.common.responses import (
    StandardResponse,
    success_response,
)
from app.core.permissions import (
    require_admin,
    require_provider,
)
from app.database.session import get_db
from app.models.provider import Provider
from app.models.user import User
from app.schemas.admin import (
    AdminLogRead,
    ProviderDetailRead,
    ProviderOnboard,
    ProviderRead,
    ProviderVerifyRequest,
    UserRead,
)
from app.services.admin_service import AdminService
from app.services.booking_service import BookingService
from app.services.provider_service import ProviderService


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


# ============================================================
# SERVICE DEPENDENCIES
# ============================================================


def _admin(
    db: AsyncSession = Depends(get_db),
) -> AdminService:
    """Build an AdminService bound to the request session."""

    return AdminService(db)


def _providers(
    db: AsyncSession = Depends(get_db),
) -> ProviderService:
    """Build a ProviderService bound to the request session."""

    return ProviderService(db)


def _bookings(
    db: AsyncSession = Depends(get_db),
) -> BookingService:
    """Build a BookingService bound to the request session."""

    return BookingService(db)


def _provider_detail(
    provider: Provider,
    owner: Optional[User],
) -> ProviderDetailRead:
    """Serialise a provider together with its account owner."""

    detail = ProviderDetailRead.model_validate(provider)

    if owner is not None:
        detail.owner = UserRead.model_validate(owner)

    return detail


# ============================================================
# PROVIDER SELF-SERVICE ONBOARDING
# ============================================================


@router.post(
    "/providers/onboard",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create my provider profile (provider)",
)
async def onboard_provider(
    payload: ProviderOnboard,
    service: ProviderService = Depends(_providers),
    user: User = Depends(require_provider),
):
    provider = await service.onboard(
        user,
        payload,
    )

    return success_response(
        data=ProviderRead.model_validate(
            provider
        ),
        message="Provider profile created.",
    )


# ============================================================
# ADMIN - USERS
# ============================================================


@router.get(
    "/users",
    response_model=StandardResponse,
    summary="List users (admin)",
)
async def list_users(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    service: AdminService = Depends(_admin),
    _admin_user: User = Depends(require_admin),
):
    users = await service.list_users(
        skip=skip,
        limit=limit,
    )

    return success_response(
        data=[
            UserRead.model_validate(user)
            for user in users
        ],
        message="Users fetched.",
    )


# ============================================================
# ADMIN - PROVIDERS
# ============================================================


@router.get(
    "/providers",
    response_model=StandardResponse,
    summary="List providers (admin)",
)
async def list_providers(
    category: Optional[str] = Query(
        default=None,
    ),
    is_verified: Optional[bool] = Query(
        default=None,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    service: AdminService = Depends(_admin),
    _admin_user: User = Depends(require_admin),
):
    providers = await service.list_providers(
        skip=skip,
        limit=limit,
        category=category,
        is_verified=is_verified,
    )

    return success_response(
        data=[
            ProviderRead.model_validate(provider)
            for provider in providers
        ],
        message="Providers fetched.",
    )


@router.get(
    "/providers/{provider_id}",
    response_model=StandardResponse,
    summary="Get a single provider application (admin)",
)
async def get_provider(
    provider_id: int,
    service: AdminService = Depends(_admin),
    _admin_user: User = Depends(require_admin),
):
    provider, owner = await service.get_provider_detail(
        provider_id
    )

    return success_response(
        data=_provider_detail(provider, owner),
        message="Provider fetched.",
    )


@router.put(
    "/providers/{provider_id}/verify",
    response_model=StandardResponse,
    summary="Verify or reject a provider (admin)",
)
async def verify_provider(
    provider_id: int,
    payload: ProviderVerifyRequest,
    service: AdminService = Depends(_admin),
    admin_user: User = Depends(require_admin),
):
    provider, owner = await service.verify_provider(
        provider_id,
        payload,
        admin_user,
    )

    return success_response(
        data=_provider_detail(provider, owner),
        message=(
            "Provider approved."
            if payload.is_verified
            else "Provider application rejected."
        ),
    )


# ============================================================
# ADMIN - BOOKINGS
# ============================================================


@router.get(
    "/bookings",
    response_model=StandardResponse,
    summary="List all platform bookings (admin)",
)
async def list_all_bookings(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    service: BookingService = Depends(_bookings),
    admin_user: User = Depends(require_admin),
):
    """
    Return all platform bookings for an administrator.

    BookingService.list_history already supports admins
    and returns every booking when no customer/provider
    filter is supplied.
    """

    params = PageParams(
        page=page,
        page_size=page_size,
    )

    bookings = await service.list_history(
        admin_user,
        params,
        as_provider=None,
        status=None,
    )

    return success_response(
        data=bookings,
        message="Bookings fetched.",
    )


# ============================================================
# ADMIN - AUDIT LOGS
# ============================================================


@router.get(
    "/audit-logs",
    response_model=StandardResponse,
    summary="List administrative audit logs (admin)",
)
async def audit_logs(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    service: AdminService = Depends(_admin),
    _admin_user: User = Depends(require_admin),
):
    logs = await service.audit_logs(
        skip=skip,
        limit=limit,
    )

    return success_response(
        data=[
            AdminLogRead.model_validate(log)
            for log in logs
        ],
        message="Audit logs fetched.",
    )