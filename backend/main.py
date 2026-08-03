from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from database.database import engine, Base
# Make sure models are loaded before Base.metadata.create_all
import database.base  # noqa

from api.routes import admin, review, dashboard, ai

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin / Auth"])
app.include_router(review.router, prefix=f"{settings.API_V1_STR}/review", tags=["Review"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard"])
app.include_router(ai.router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Integration"])

@app.get("/")
def root():
    return {"message": "Welcome to the Service Provider API. Visit /docs for Swagger documentation."}
