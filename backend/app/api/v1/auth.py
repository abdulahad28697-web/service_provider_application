"""HTTP endpoints for authentication (register / login)."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import StandardResponse, success_response
from app.database.session import get_db
from app.schemas.auth import Token, UserLogin, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Build an :class:`AuthService` bound to the request session."""
    return AuthService(db)


@router.post(
    "/register",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register(
    payload: UserRegister,
    service: AuthService = Depends(_service),
):
    user = await service.register(payload)
    return success_response(
        data={"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role.value},
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
    user = await service.authenticate(payload.email, payload.password)
    token = service.issue_token(user)
    return success_response(
        data=Token(access_token=token, token_type="bearer"),
        message="Login successful.",
    )
