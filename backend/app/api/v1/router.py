"""Aggregation of all v1 routers.

The combined router is mounted by the application factory under
``settings.API_V1_PREFIX`` (e.g. ``/api/v1``).
"""
from fastapi import APIRouter

from app.api.v1 import bookings, categories, services

api_router = APIRouter()

# Mount each feature router. Prefixes are declared on the routers themselves
# (e.g. ``/bookings``), so they slot in cleanly under the shared v1 prefix.
api_router.include_router(categories.router)
api_router.include_router(services.router)
api_router.include_router(bookings.router)
