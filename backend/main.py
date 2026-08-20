"""ServiceHub AI backend entry point.

Run locally:  ``uvicorn main:app --reload``
Run in Docker: ``docker compose up``
"""
import os
from contextlib import asynccontextmanager
import time
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.uploads.utils import ensure_upload_directories
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict


import app.models

from app.api.v1.router import api_router
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
        if request.url.path in ("/", "/health") or request.url.path.startswith("/media"):
            return await call_next(request)

        if settings.DEBUG:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        minute_ago = now - 60
        client_requests = self.requests[client_ip]

        while client_requests and client_requests[0] < minute_ago:
            client_requests.pop(0)

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

        client_requests.append(now)

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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

    register_exception_handlers(application)

    application.add_middleware(SecurityHeadersMiddleware)

    application.add_middleware(RateLimitMiddleware, requests_per_minute=120)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://[a-zA-Z0-9-]+\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
    async def health():
        return {"status": "healthy"}

    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "frontend",
        "dist"
    )

    if os.path.exists(frontend_dist):
        assets_dir = os.path.join(frontend_dist, "assets")

        if os.path.exists(assets_dir):
            application.mount(
                "/assets",
                StaticFiles(directory=assets_dir),
                name="static_assets"
            )

        @application.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            if full_path.startswith("api/") or full_path.startswith("media/"):
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Not Found"}
                )

            target_file = os.path.join(frontend_dist, full_path)

            if full_path and os.path.exists(target_file) and os.path.isfile(target_file):
                return FileResponse(target_file)

            return FileResponse(os.path.join(frontend_dist, "index.html"))

    else:
        @application.get("/", tags=["Health"])
        async def root():
            return {
                "service": settings.PROJECT_NAME,
                "status": "ok"
            }

    return application


app = create_app()