"""HTTP endpoints for admin operations and provider onboarding."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import StandardResponse, success_response
from app.core.permissions import require_admin, require_provider
from app.database.session import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminLogRead,
    ProviderOnboard,
    ProviderRead,
    ProviderVerifyRequest,
    UserRead,
)
from app.services.admin_service import AdminService
from app.services.provider_service import ProviderService

router = APIRouter(prefix="/admin", tags=["Admin"])


def _admin(db: AsyncSession = Depends(get_db)) -> AdminService:
    """Build an :class:`AdminService` bound to the request session."""
    return AdminService(db)


def _providers(db: AsyncSession = Depends(get_db)) -> ProviderService:
    """Build a :class:`ProviderService` bound to the request session."""
    return ProviderService(db)


# --------------------------------------------------------------------------- #
# Provider self-service onboarding
# --------------------------------------------------------------------------- #
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
    provider = await service.onboard(user, payload)
    return success_response(
        data=ProviderRead.model_validate(provider), message="Provider profile created."
    )


# --------------------------------------------------------------------------- #
# Admin-only management
# --------------------------------------------------------------------------- #
@router.get(
    "/users",
    response_model=StandardResponse,
    summary="List users (admin)",
)
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: AdminService = Depends(_admin),
    _admin_user: User = Depends(require_admin),
):
    users = await service.list_users(skip=skip, limit=limit)
    return success_response(
        data=[UserRead.model_validate(u) for u in users], message="Users fetched."
    )


@router.get(
    "/providers",
    response_model=StandardResponse,
    summary="List providers (admin)",
)
async def list_providers(
    category: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: AdminService = Depends(_admin),
    _admin_user: User = Depends(require_admin),
):
    providers = await service.list_providers(skip=skip, limit=limit, category=category)
    return success_response(
        data=[ProviderRead.model_validate(p) for p in providers],
        message="Providers fetched.",
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
    provider = await service.verify_provider(provider_id, payload, admin_user)
    return success_response(
        data=ProviderRead.model_validate(provider), message="Provider updated."
    )


@router.get(
    "/audit-logs",
    response_model=StandardResponse,
    summary="List administrative audit logs (admin)",
)
async def audit_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: AdminService = Depends(_admin),
    _admin_user: User = Depends(require_admin),
):
    logs = await service.audit_logs(skip=skip, limit=limit)
    return success_response(
        data=[AdminLogRead.model_validate(log) for log in logs],
        message="Audit logs fetched.",
    )
