from sqlalchemy.orm import Session
from models.provider import Provider
from schemas.admin.request import ProviderCreate

class ProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, provider_id: int) -> Provider | None:
        return self.db.query(Provider).filter(Provider.id == provider_id).first()

    def get_by_user_id(self, user_id: int) -> Provider | None:
        return self.db.query(Provider).filter(Provider.user_id == user_id).first()

    def get_all(self, skip: int = 0, limit: int = 100, category: str | None = None) -> list[Provider]:
        query = self.db.query(Provider)
        if category:
            query = query.filter(Provider.category.ilike(f"%{category}%"))
        return query.offset(skip).limit(limit).all()

    def create(self, user_id: int, provider_create: ProviderCreate) -> Provider:
        db_provider = Provider(
            user_id=user_id,
            bio=provider_create.bio,
            business_name=provider_create.business_name,
            category=provider_create.category,
            hourly_rate=provider_create.hourly_rate
        )
        self.db.add(db_provider)
        self.db.commit()
        self.db.refresh(db_provider)
        return db_provider

    def update_verification(self, provider_id: int, is_verified: bool) -> Provider | None:
        db_provider = self.get_by_id(provider_id)
        if db_provider:
            db_provider.is_verified = is_verified
            self.db.commit()
            self.db.refresh(db_provider)
        return db_provider

    def update_rating(self, provider_id: int, new_rating: float) -> Provider | None:
        db_provider = self.get_by_id(provider_id)
        if db_provider:
            db_provider.rating = new_rating
            self.db.commit()
            self.db.refresh(db_provider)
        return db_provider
