from sqlalchemy.orm import Session
from models.provider import Provider
from models.service import Service

class AIRepository:
    def __init__(self, db: Session):
        self.db = db

    def search_providers_by_keyword(self, keyword: str, limit: int = 5) -> list[Provider]:
        # Search bio or category or business name
        return self.db.query(Provider)\
            .filter(
                (Provider.bio.ilike(f"%{keyword}%")) | 
                (Provider.category.ilike(f"%{keyword}%")) | 
                (Provider.business_name.ilike(f"%{keyword}%"))
            )\
            .limit(limit)\
            .all()

    def search_services_by_price(self, max_price: float, limit: int = 5) -> list[Service]:
        return self.db.query(Service)\
            .filter(Service.price <= max_price)\
            .limit(limit)\
            .all()
