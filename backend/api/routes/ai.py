from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.ai.request import ChatbotMessageRequest, RecommendationRequest
from schemas.ai.response import ChatbotResponse, RecommendationResponse
from schemas.admin.response import ProviderResponse
from services.ai.chatbot_service import ChatbotService
from services.ai.recommendation_service import RecommendationService
from services.ai.analytics_service import AnalyticsService
from services.ai.search_service import SearchService
from api.dependencies import get_current_user
from models.user import User

router = APIRouter()

@router.post("/chatbot", response_model=ChatbotResponse)
def chatbot_interaction(
    request: ChatbotMessageRequest,
    db: Session = Depends(get_db)
):
    chatbot_service = ChatbotService(db)
    return chatbot_service.process_message(request)

@router.post("/recommend", response_model=RecommendationResponse)
def recommend_providers(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    rec_service = RecommendationService(db)
    return rec_service.get_recommendations(request)

@router.get("/trends")
def market_trends(
    db: Session = Depends(get_db)
):
    analytics_service = AnalyticsService(db)
    return analytics_service.get_market_trends()

@router.get("/search", response_model=list[ProviderResponse])
def search_providers(
    q: str | None = None,
    category: str | None = None,
    min_rate: float | None = None,
    max_rate: float | None = None,
    db: Session = Depends(get_db)
):
    search_service = SearchService(db)
    return search_service.search_providers(q, category, min_rate, max_rate)