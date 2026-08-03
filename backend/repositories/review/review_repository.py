from sqlalchemy.orm import Session
from models.review import Review
from schemas.review.request import ReviewCreate

class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, review_id: int) -> Review | None:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_by_booking_id(self, booking_id: int) -> Review | None:
        return self.db.query(Review).filter(Review.booking_id == booking_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Review]:
        return self.db.query(Review).offset(skip).limit(limit).all()

    def create(self, client_id: int, review_create: ReviewCreate) -> Review:
        db_review = Review(
            booking_id=review_create.booking_id,
            client_id=client_id,
            rating=review_create.rating,
            comment=review_create.comment
        )
        self.db.add(db_review)
        self.db.commit()
        self.db.refresh(db_review)
        return db_review

    def get_average_rating_for_provider(self, provider_id: int) -> float:
        # Join review -> booking -> service to filter by provider_id
        from models.booking import Booking
        from models.service import Service
        from sqlalchemy import func

        result = self.db.query(func.avg(Review.rating))\
            .join(Booking, Review.booking_id == Booking.id)\
            .join(Service, Booking.service_id == Service.id)\
            .filter(Service.provider_id == provider_id)\
            .scalar()
        
        return float(result) if result else 0.0
