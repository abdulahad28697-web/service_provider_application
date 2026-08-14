"""HTTP endpoints for the AI user assistant."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import StandardResponse, success_response
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.admin import ProviderRead
from app.schemas.ai import (
    BookingAssistanceRequest,
    BookingAssistanceResponse,
    ChatbotMessageRequest,
    ChatbotResponse,
    FAQRequest,
    FAQResponse,
    PersonalizedSuggestionResponse,
    RecommendationRequest,
    RecommendationResponse,
    ServiceComparisonRequest,
    ServiceComparisonResponse,
    ServiceRecommendationRequest,
    ServiceRecommendationResponse,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def _service(
    db: AsyncSession = Depends(get_db),
) -> AIService:
    """Build the AI service for the current request."""
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
        data=ChatbotResponse.model_validate(response),
        message="Reply generated.",
    )

@router.post(
    "/recommend",
    response_model=StandardResponse,
    include_in_schema=False,
)


@router.post(
    "/recommend/providers",
    response_model=StandardResponse,
    summary="Get provider recommendations",
)
async def recommend_providers(
    payload: RecommendationRequest,
    service: AIService = Depends(_service),
):
    recommendations = await service.recommend(payload)

    return success_response(
        data=RecommendationResponse.model_validate(recommendations),
        message="Provider recommendations generated.",
    )

async def recommend_services(
    payload: ServiceRecommendationRequest,
    service: AIService = Depends(_service),
):
    recommendations = await service.recommend_services(payload)

    return success_response(
        data=ServiceRecommendationResponse.model_validate(
            recommendations
        ),
        message="Service recommendations generated.",
    )


@router.post(
    "/faq",
    response_model=StandardResponse,
    summary="Ask the FAQ assistant",
)
async def faq_assistant(
    payload: FAQRequest,
    service: AIService = Depends(_service),
):
    response = await service.answer_faq(payload)

    return success_response(
        data=FAQResponse.model_validate(response),
        message="FAQ answer generated.",
    )


@router.post(
    "/booking-assistance",
    response_model=StandardResponse,
    summary="Get booking assistance",
)
async def booking_assistance(
    payload: BookingAssistanceRequest,
    service: AIService = Depends(_service),
    _user: User = Depends(get_current_user),
):
    response = await service.booking_assistance(payload)

    return success_response(
        data=BookingAssistanceResponse.model_validate(response),
        message="Booking guidance generated.",
    )


@router.post(
    "/compare-services",
    response_model=StandardResponse,
    summary="Compare services",
)
async def compare_services(
    payload: ServiceComparisonRequest,
    service: AIService = Depends(_service),
):
    comparison = await service.compare_services(payload)

    return success_response(
        data=ServiceComparisonResponse.model_validate(comparison),
        message="Services compared.",
    )


@router.get(
    "/personalized",
    response_model=StandardResponse,
    summary="Get personalized suggestions",
)
async def personalized_suggestions(
    service: AIService = Depends(_service),
    user: User = Depends(get_current_user),
):
    suggestions = await service.personalized_suggestions(user)

    return success_response(
        data=PersonalizedSuggestionResponse.model_validate(
            suggestions
        ),
        message="Personalized suggestions generated.",
    )


@router.get(
    "/trends",
    response_model=StandardResponse,
    summary="Get market demand trends",
)
async def trends(
    service: AIService = Depends(_service),
):
    data = await service.market_trends()

    return success_response(
        data=data,
        message="Trends fetched.",
    )


@router.get(
    "/search",
    response_model=StandardResponse,
    summary="Natural-language provider search",
)
async def search(
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    min_rate: Optional[float] = Query(default=None, ge=0),
    max_rate: Optional[float] = Query(default=None, ge=0),
    service: AIService = Depends(_service),
):
    providers = await service.search_providers(
        query=q,
        category=category,
        min_rate=min_rate,
        max_rate=max_rate,
    )

    return success_response(
        data=[
            ProviderRead.model_validate(provider)
            for provider in providers
        ],
        message="Providers fetched.",
    )