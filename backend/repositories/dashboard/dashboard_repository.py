from sqlalchemy.orm import Session
from sqlalchemy import func
from models.user import User
from models.provider import Provider
from models.booking import Booking
from models.review import Review
from models.service import Service
from schemas.dashboard.response import BookingSummary
from datetime import datetime

class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self, start_date: datetime | None = None, end_date: datetime | None = None):
        # Build query for bookings
        booking_query = self.db.query(Booking)
        if start_date:
            booking_query = booking_query.filter(Booking.created_at >= start_date)
        if end_date:
            booking_query = booking_query.filter(Booking.created_at <= end_date)

        total_bookings = booking_query.count()

        # Total revenue
        revenue_query = self.db.query(func.sum(Booking.price)).filter(Booking.status == "completed")
        if start_date:
            revenue_query = revenue_query.filter(Booking.created_at >= start_date)
        if end_date:
            revenue_query = revenue_query.filter(Booking.created_at <= end_date)
        
        total_revenue = revenue_query.scalar() or 0.0

        # Totals
        total_users = self.db.query(User).count()
        total_providers = self.db.query(Provider).count()

        # Average rating across reviews
        avg_rating = self.db.query(func.avg(Review.rating)).scalar() or 0.0

        # Recent Bookings (limit to 5)
        recent_db_bookings = self.db.query(Booking)\
            .order_by(Booking.created_at.desc())\
            .limit(5)\
            .all()

        recent_bookings = []
        for b in recent_db_bookings:
            client_name = b.client.full_name if b.client else "Unknown"
            service_name = b.service.name if b.service else "Unknown"
            recent_bookings.append(
                BookingSummary(
                    id=b.id,
                    client_name=client_name,
                    service_name=service_name,
                    price=b.price,
                    status=b.status,
                    scheduled_at=b.scheduled_at.isoformat()
                )
            )

        return {
            "total_bookings": total_bookings,
            "total_revenue": float(total_revenue),
            "total_users": total_users,
            "total_providers": total_providers,
            "average_rating": float(avg_rating),
            "recent_bookings": recent_bookings
        }
