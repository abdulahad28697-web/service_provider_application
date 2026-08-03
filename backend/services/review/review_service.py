from sqlalchemy.orm import Session
from repositories.review.review_repository import ReviewRepository
from repositories.admin.provider_repository import ProviderRepository
from schemas.review.request import ReviewCreate
from core.exceptions import EntityAlreadyExistsException, EntityNotFoundException
from models.review import Review
from models.booking import Booking
from models.service import Service

class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.review_repo = ReviewRepository(db)
        self.provider_repo = ProviderRepository(db)

    def create_review(self, client_id: int, review_create: ReviewCreate) -> Review:
        # Check if review already exists for booking
        existing = self.review_repo.get_by_booking_id(review_create.booking_id)
        if existing:
            raise EntityAlreadyExistsException("Review", "booking_id", review_create.booking_id)

        # Get booking to find service & provider
        booking = self.db.query(Booking).filter(Booking.id == review_create.booking_id).first()
        if not booking:
            raise EntityNotFoundException("Booking", review_create.booking_id)
        if booking.client_id != client_id:
            raise EntityNotFoundException("Booking associated with this client", review_create.booking_id)

        # Create review
        new_review = self.review_repo.create(client_id, review_create)

        # Update average rating of provider
        service = self.db.query(Service).filter(Service.id == booking.service_id).first()
        if service:
            avg_rating = self.review_repo.get_average_rating_for_provider(service.provider_id)
            self.provider_repo.update_rating(service.provider_id, avg_rating)

        return new_review

    def list_reviews(self, skip: int = 0, limit: int = 100) -> list[Review]:
        return self.review_repo.get_all(skip, limit)
