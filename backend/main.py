"""ServiceHub AI backend entry point.

Run locally:  ``uvicorn main:app --reload``
Run in Docker: ``docker compose up``
"""
from contextlib import asynccontextmanager
import time
from fastapi.staticfiles import StaticFiles
from app.uploads.utils import ensure_upload_directories
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict

# Importing the models package registers every ORM model with Base.metadata so
# that create_all (below) sees the full schema.
import app.models  # noqa: F401

from app.api.v1.router import api_router  # noqa: E402
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.database.base import Base
from app.database.database import engine


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter for API endpoints."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: defaultdict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ("/", "/health") or request.url.path.startswith("/media"):
            return await call_next(request)

        # Skip if in debug mode
        if settings.DEBUG:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Clean old entries and count recent requests
        now = time.time()
        minute_ago = now - 60
        client_requests = self.requests[client_ip]

        # Remove requests older than 1 minute
        while client_requests and client_requests[0] < minute_ago:
            client_requests.pop(0)

        # Check rate limit
        if len(client_requests) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Rate limit exceeded. Please try again later.",
                    "data": None
                },
                headers={"Retry-After": "60"}
            )

        # Record this request
        client_requests.append(now)

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Only add HSTS and CSP in production (not debug)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            # Basic CSP - adjust as needed for your frontend
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup. For production, prefer Alembic migrations; this
    # keeps the Docker bring-up zero-config for the assignment.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description="AI-based service provider & booking platform.",
        lifespan=lifespan,
    )

    ensure_upload_directories()

    application.mount(
        "/media",
        StaticFiles(directory="media"),
        name="media",
    )

    # Uniform error envelope for our domain exceptions + validation errors.
    register_exception_handlers(application)

    # Add security headers middleware (should be early)
    application.add_middleware(SecurityHeadersMiddleware)

    # Add rate limiting middleware
    application.add_middleware(RateLimitMiddleware, requests_per_minute=120)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the aggregated v1 API under the configured prefix.
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get("/", tags=["Health"])
    async def root():
        return {"service": settings.PROJECT_NAME, "status": "ok"}

    @application.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
    async def health():
        return {"status": "healthy"}

    return application


app = create_app()
