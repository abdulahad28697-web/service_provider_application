from sqlalchemy.orm import Session
from repositories.admin.provider_repository import ProviderRepository
from repositories.admin.user_repository import UserRepository
from repositories.admin.report_repository import ReportRepository
from schemas.admin.request import ProviderCreate
from core.exceptions import EntityNotFoundException, PermissionDeniedException, EntityAlreadyExistsException
from models.provider import Provider

class ProviderService:
    def __init__(self, db: Session):
        self.provider_repo = ProviderRepository(db)
        self.user_repo = UserRepository(db)
        self.report_repo = ReportRepository(db)

    def onboard_provider(self, user_id: int, provider_create: ProviderCreate) -> Provider:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        if user.role != "provider":
            raise PermissionDeniedException("User role must be provider to onboard as provider")
        
        existing = self.provider_repo.get_by_user_id(user_id)
        if existing:
            raise EntityAlreadyExistsException("Provider profile", "user_id", user_id)
            
        return self.provider_repo.create(user_id, provider_create)

    def verify_provider(self, provider_id: int, is_verified: bool, admin_user_id: int) -> Provider:
        provider = self.provider_repo.get_by_id(provider_id)
        if not provider:
            raise EntityNotFoundException("Provider", provider_id)
        
        updated_provider = self.provider_repo.update_verification(provider_id, is_verified)
        
        # Log action
        self.report_repo.log_action(
            action="VERIFY_PROVIDER",
            performed_by=admin_user_id,
            details=f"Provider ID: {provider_id}, Business: {provider.business_name}, Verified: {is_verified}"
        )
        
        return updated_provider

    def get_provider_by_id(self, provider_id: int) -> Provider | None:
        return self.provider_repo.get_by_id(provider_id)

    def list_providers(self, skip: int = 0, limit: int = 100, category: str | None = None) -> list[Provider]:
        return self.provider_repo.get_all(skip, limit, category)
