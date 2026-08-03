"""AI assistant Pydantic schemas (chatbot / recommendations)."""
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatbotMessageRequest(BaseModel):
    """A message sent to the AI assistant."""

    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None


class ChatbotResponse(BaseModel):
    """The assistant's reply plus suggested follow-up actions."""

    response: str
    suggested_actions: List[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    """Criterion for AI provider recommendations."""

    query: str = Field(..., min_length=1)
    category: Optional[str] = None
    max_price: Optional[Decimal] = None
    limit: int = Field(default=5, ge=1, le=20)


class RecommendedProvider(BaseModel):
    """A single AI-recommended provider with a human-readable reason."""

    provider_id: int
    business_name: Optional[str] = None
    category: str
    hourly_rate: Decimal
    rating: Decimal
    reason: str


class RecommendationResponse(BaseModel):
    """The list of AI-recommended providers."""

    recommendations: List[RecommendedProvider]
