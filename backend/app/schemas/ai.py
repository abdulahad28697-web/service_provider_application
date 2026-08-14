"""Pydantic schemas for the AI user assistant."""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatbotMessageRequest(BaseModel):
    """A message sent to the assistant."""

    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = Field(default=None, max_length=100)


class ChatbotResponse(BaseModel):
    """Assistant reply with possible next actions."""

    response: str
    suggested_actions: List[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    """Criteria for provider recommendations."""

    query: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=120)
    max_price: Optional[Decimal] = Field(default=None, ge=0)
    limit: int = Field(default=5, ge=1, le=20)


class RecommendedProvider(BaseModel):
    """A recommended provider and its recommendation reason."""

    provider_id: int
    business_name: Optional[str] = None
    category: str
    hourly_rate: Decimal
    rating: Decimal
    reason: str


class RecommendationResponse(BaseModel):
    """Recommended provider collection."""

    recommendations: List[RecommendedProvider]


class ServiceRecommendationRequest(BaseModel):
    """Criteria for service recommendations."""

    query: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, max_length=120)
    max_price: Optional[Decimal] = Field(default=None, ge=0)
    limit: int = Field(default=5, ge=1, le=20)


class RecommendedService(BaseModel):
    """A recommended service and its reason."""

    service_id: int
    provider_id: int
    title: str
    description: str
    price: Decimal
    price_unit: str
    duration_minutes: int
    reason: str


class ServiceRecommendationResponse(BaseModel):
    """Recommended service collection."""

    recommendations: List[RecommendedService]


class FAQRequest(BaseModel):
    """A natural-language FAQ question."""

    question: str = Field(..., min_length=1, max_length=500)


class FAQResponse(BaseModel):
    """FAQ answer returned by the assistant."""

    answer: str
    matched_topic: str
    suggested_actions: List[str] = Field(default_factory=list)


class BookingAssistanceRequest(BaseModel):
    """User message requesting help with a booking."""

    message: str = Field(..., min_length=1, max_length=1000)
    service_id: Optional[int] = Field(default=None, gt=0)


class BookingAssistanceResponse(BaseModel):
    """Structured guidance for completing a booking."""

    response: str
    service_id: Optional[int] = None
    required_information: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


class ServiceComparisonRequest(BaseModel):
    """IDs of services the user wants to compare."""

    service_ids: List[int] = Field(..., min_length=2, max_length=5)


class ComparedService(BaseModel):
    """Service fields included in a comparison."""

    service_id: int
    provider_id: int
    title: str
    price: Decimal
    price_unit: str
    duration_minutes: int
    is_featured: bool


class ServiceComparisonResponse(BaseModel):
    """Comparison result and assistant summary."""

    services: List[ComparedService]
    summary: str
    best_value_service_id: Optional[int] = None


class PersonalizedSuggestionResponse(BaseModel):
    """Suggestions based on the current user's booking history."""

    preferred_categories: List[str] = Field(default_factory=list)
    service_recommendations: List[RecommendedService] = Field(
        default_factory=list
    )
    provider_recommendations: List[RecommendedProvider] = Field(
        default_factory=list
    )
    message: str