"""HTTP endpoints for the AI assistant (chatbot / recommendations / trends / search)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import StandardResponse, success_response
from app.database.session import get_db
from app.schemas.ai import (
    ChatbotMessageRequest,
    ChatbotResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas.admin import ProviderRead
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def _service(db: AsyncSession = Depends(get_db)) -> AIService:
    """Build an :class:`AIService` bound to the request session."""
    return AIService(db)


@router.post(
    "/chatbot",
    response_model=StandardResponse,
    summary="Chat with the AI assistant",
)
async def chatbot(
    payload: ChatbotMessageRequest,
    service: AIService = Depends(_service),
):
    response = await service.chatbot(payload)
    return success_response(
        data=ChatbotResponse.model_validate(response), message="Reply generated."
    )


@router.post(
    "/recommend",
    response_model=StandardResponse,
    summary="Get AI provider recommendations",
)
async def recommend(
    payload: RecommendationRequest,
    service: AIService = Depends(_service),
):
    recs = await service.recommend(payload)
    return success_response(
        data=RecommendationResponse.model_validate(recs), message="Recommendations generated."
    )


@router.get(
    "/trends",
    response_model=StandardResponse,
    summary="Get market demand trends by category",
)
async def trends(
    service: AIService = Depends(_service),
):
    data = await service.market_trends()
    return success_response(data=data, message="Trends fetched.")


@router.get(
    "/search",
    response_model=StandardResponse,
    summary="Search providers",
)
async def search(
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    min_rate: Optional[float] = Query(default=None, ge=0),
    max_rate: Optional[float] = Query(default=None, ge=0),
    service: AIService = Depends(_service),
):
    providers = await service.search_providers(
        query=q, category=category, min_rate=min_rate, max_rate=max_rate
    )
    return success_response(
        data=[ProviderRead.model_validate(p) for p in providers],
        message="Providers fetched.",
    )
