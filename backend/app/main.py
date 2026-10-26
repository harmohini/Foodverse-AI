"""FoodVerse AI — FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.database.connection import init_db
from app.api.routes import health, food, nutrition, freshness, hygiene, cooking, meal_plans, history

setup_logging(settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.info(f"AI provider: {settings.ai_provider} | Demo mode: {settings.is_demo_mode}")
    init_db()
    logger.info("Database initialized.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Multimodal Food Intelligence Platform — analyze food images, videos, audio, and text.",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(health.router, prefix="/api")
app.include_router(food.router)
app.include_router(nutrition.router)
app.include_router(freshness.router)
app.include_router(hygiene.router)
app.include_router(cooking.router)
app.include_router(meal_plans.router)
app.include_router(history.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "running",
        "demo_mode": settings.is_demo_mode,
        "docs": "/docs",
    }
