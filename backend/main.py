"""ServiceHub AI backend entry point.

Run locally:  ``uvicorn main:app --reload``
Run in Docker: ``docker compose up``
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing the models package registers every ORM model with Base.metadata so
# that create_all (below) sees the full schema.
import app.models  # noqa: F401

from app.api.v1.router import api_router  # noqa: E402
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.database.base import Base
from app.database.database import engine


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

    # Uniform error envelope for our domain exceptions + validation errors.
    register_exception_handlers(application)

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
