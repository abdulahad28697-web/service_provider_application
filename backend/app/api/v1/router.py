"""Aggregation of all v1 routers.

The combined router is mounted by the application factory under
``settings.API_V1_PREFIX`` (e.g. ``/api/v1``).
"""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    ai,
    auth,
    bookings,
    categories,
    dashboard,
    reviews,
    services,
    users,
)

api_router = APIRouter()

# Mount each feature router. Prefixes are declared on the routers themselves
# (e.g. ``/bookings``), so they slot in cleanly under the shared v1 prefix.
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(services.router)
api_router.include_router(bookings.router)
api_router.include_router(admin.router)
api_router.include_router(reviews.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
