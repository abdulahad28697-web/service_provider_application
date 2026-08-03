from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from schemas.review.request import ReviewCreate
from schemas.review.response import ReviewResponse
from services.review.review_service import ReviewService
from api.dependencies import get_current_user, RoleRequired
from core.permissions import UserRole
from models.user import User

router = APIRouter()

@router.post("", response_model=ReviewResponse)
def create_review(
    review_create: ReviewCreate,
    current_user: User = Depends(RoleRequired([UserRole.CLIENT])),
    db: Session = Depends(get_db)
):
    review_service = ReviewService(db)
    return review_service.create_review(current_user.id, review_create)

@router.get("", response_model=list[ReviewResponse])
def get_reviews(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    review_service = ReviewService(db)
    return review_service.list_reviews(skip, limit)