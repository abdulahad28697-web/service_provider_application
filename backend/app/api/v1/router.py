"""Aggregation of all v1 API routers."""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai,
    auth,
    bookings,
    categories,
    dashboard,
    providers,
    reviews,
    services,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(providers.router)
api_router.include_router(categories.router)
api_router.include_router(services.router)
api_router.include_router(bookings.router)
api_router.include_router(admin.router)
api_router.include_router(reviews.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)