"""HTTP endpoints for reviews."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import StandardResponse, success_response
from app.core.permissions import require_customer
from app.database.session import get_db
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewRead
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    """Build a :class:`ReviewService` bound to the request session."""
    return ReviewService(db)


@router.post(
    "",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Leave a review on a completed booking",
)
async def create_review(
    payload: ReviewCreate,
    service: ReviewService = Depends(_service),
    customer: User = Depends(require_customer),
):
    review = await service.create(customer, payload)
    return success_response(
        data=ReviewRead.model_validate(review), message="Review created."
    )


@router.get(
    "",
    response_model=StandardResponse,
    summary="List reviews",
)
async def list_reviews(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: ReviewService = Depends(_service),
):
    reviews = await service.list(skip=skip, limit=limit)
    return success_response(
        data=[ReviewRead.model_validate(r) for r in reviews], message="Reviews fetched."
    )
