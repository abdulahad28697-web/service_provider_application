from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.admin.request import UserCreate, ProviderCreate, ProviderVerifyRequest
from schemas.admin.response import UserResponse, ProviderResponse, AdminLogResponse
from schemas.admin.common import Token
from services.admin.user_service import UserService
from services.admin.provider_service import ProviderService
from services.admin.report_service import ReportService
from api.dependencies import get_current_user, RoleRequired
from core.permissions import UserRole
from core.security import create_access_token
from models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.register_user(user_create)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/onboard-provider", response_model=ProviderResponse)
def onboard_provider(
    provider_create: ProviderCreate,
    current_user: User = Depends(RoleRequired([UserRole.PROVIDER])),
    db: Session = Depends(get_db)
):
    provider_service = ProviderService(db)
    return provider_service.onboard_provider(current_user.id, provider_create)

@router.put("/verify-provider/{provider_id}", response_model=ProviderResponse)
def verify_provider(
    provider_id: int,
    verify_req: ProviderVerifyRequest,
    current_user: User = Depends(RoleRequired([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    provider_service = ProviderService(db)
    return provider_service.verify_provider(provider_id, verify_req.is_verified, current_user.id)

@router.get("/audit-logs", response_model=list[AdminLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(RoleRequired([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    report_service = ReportService(db)
    return report_service.get_audit_logs(skip, limit)