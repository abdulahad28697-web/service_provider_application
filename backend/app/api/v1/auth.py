"""HTTP endpoints for authentication."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import (
    StandardResponse,
    success_response,
)
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserLogin,
    UserRegister,
)
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """Build an AuthService for the request session."""
    return AuthService(db)


@router.post(
    "/register",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
async def register(
    payload: UserRegister,
    service: AuthService = Depends(_service),
):
    user = await service.register(payload)

    return success_response(
        data={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
        },
        message="Account created.",
    )


@router.post(
    "/login",
    response_model=StandardResponse,
    summary="Login and receive an access token",
)
async def login(
    payload: UserLogin,
    service: AuthService = Depends(_service),
):
    user = await service.authenticate(
        str(payload.email),
        payload.password,
    )

    token = service.issue_token(user)

    return success_response(
        data=Token(
            access_token=token,
            token_type="bearer",
        ),
        message="Login successful.",
    )


@router.post(
    "/change-password",
    response_model=StandardResponse,
    summary="Change the authenticated user's password",
)
async def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(_service),
):
    await service.change_password(
        user,
        payload,
    )

    return success_response(
        data=None,
        message="Password changed successfully.",
    )


@router.post(
    "/forgot-password",
    response_model=StandardResponse,
    summary="Request password-reset instructions",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(_service),
):
    token = await service.request_password_reset(str(payload.email))

    if token:
        print(f"\n[DEV ONLY] PASSWORD RESET TOKEN FOR {payload.email}: {token}\n", flush=True)

    return success_response(
        data={"reset_token": token} if settings.DEBUG else None,
        message=(
            "If an active account with this email exists, "
            "password-reset instructions have been sent."
        ),
    )


@router.post(
    "/reset-password",
    response_model=StandardResponse,
    summary="Reset a password using a reset token",
)
async def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(_service),
):
    await service.reset_password(payload)

    return success_response(
        data=None,
        message="Password reset successfully.",
    )