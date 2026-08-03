from sqlalchemy.orm import Session
from models.provider import Provider

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search_providers(self, query: str | None = None, category: str | None = None, min_rate: float | None = None, max_rate: float | None = None) -> list[Provider]:
        db_query = self.db.query(Provider)
        
        if query:
            db_query = db_query.filter(
                (Provider.business_name.ilike(f"%{query}%")) |
                (Provider.bio.ilike(f"%{query}%"))
            )
        
        if category:
            db_query = db_query.filter(Provider.category.ilike(f"%{category}%"))
            
        if min_rate is not None:
            db_query = db_query.filter(Provider.hourly_rate >= min_rate)
            
        if max_rate is not None:
            db_query = db_query.filter(Provider.hourly_rate <= max_rate)
            
        # Default sorting by rating
        return db_query.order_by(Provider.rating.desc()).all()
