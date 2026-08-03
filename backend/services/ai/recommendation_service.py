from sqlalchemy.orm import Session
from schemas.ai.request import RecommendationRequest
from schemas.ai.response import RecommendationResponse, RecommendedProvider
from repositories.ai.ai_repository import AIRepository

class RecommendationService:
    def __init__(self, db: Session):
        self.ai_repo = AIRepository(db)

    def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        db_providers = self.ai_repo.search_providers_by_keyword(request.query, limit=request.limit)
        
        recs = []
        for p in db_providers:
            # Create a smart recommendation reason
            reason = f"Highly rated in {p.category} with a solid {p.rating or 5.0} rating."
            if p.hourly_rate <= 50:
                reason += " Exceptionally budget-friendly hourly rate."
            if p.is_verified:
                reason += " Background checked and verified provider."
                
            recs.append(
                RecommendedProvider(
                    provider_id=p.id,
                    business_name=p.business_name,
                    category=p.category,
                    hourly_rate=p.hourly_rate,
                    rating=p.rating,
                    reason=reason
                )
            )

        # Fallback if no providers found, generate a mock or empty list
        if not recs:
            # Let's see if there are any general providers in the database to return
            from models.provider import Provider
            all_p = self.ai_repo.db.query(Provider).limit(request.limit).all()
            for p in all_p:
                recs.append(
                    RecommendedProvider(
                        provider_id=p.id,
                        business_name=p.business_name,
                        category=p.category,
                        hourly_rate=p.hourly_rate,
                        rating=p.rating,
                        reason="Suggested popular alternative provider in our system."
                    )
                )

        return RecommendationResponse(recommendations=recs)
