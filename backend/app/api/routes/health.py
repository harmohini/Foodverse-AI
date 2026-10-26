"""Health check endpoints."""
from fastapi import APIRouter
from app.schemas.schemas import HealthResponse
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        version=settings.version,
        ai_provider=settings.ai_provider,
        is_demo_mode=settings.is_demo_mode,
        message="FoodVerse AI is running." if not settings.is_demo_mode else "FoodVerse AI is running in DEMO MODE.",
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness():
    return HealthResponse(
        status="ready",
        version=settings.version,
        ai_provider=settings.ai_provider,
        is_demo_mode=settings.is_demo_mode,
        message="Ready.",
    )


@router.get("/health/provider")
async def provider_status():
    """
    Test whether the configured AI provider is actually reachable.
    Returns a lightweight connectivity result — does NOT expose API keys.
    """
    if settings.is_demo_mode:
        return {
            "provider": "demo",
            "configured": False,
            "reachable": False,
            "mode": "demo",
            "detail": "Running in Demo Mode. No AI provider is configured.",
        }

    if settings.ai_provider == "openai":
        if not settings.openai_api_key:
            return {
                "provider": "openai",
                "configured": False,
                "reachable": False,
                "mode": "demo",
                "detail": "OPENAI_API_KEY is not set. Running in Demo Mode.",
            }
        # Attempt a minimal API call to verify reachability
        try:
            import openai
            client = openai.AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
            # List models — lightweight, no tokens consumed
            await client.models.list()
            return {
                "provider": "openai",
                "configured": True,
                "reachable": True,
                "mode": "live",
                "model": settings.openai_text_model,
                "detail": "OpenAI API is reachable and responding.",
            }
        except Exception as exc:
            logger.warning(f"Provider connectivity check failed: {exc}")
            return {
                "provider": "openai",
                "configured": True,
                "reachable": False,
                "mode": "degraded",
                "detail": f"OpenAI API key is set but the API did not respond: {type(exc).__name__}",
            }

    return {
        "provider": settings.ai_provider,
        "configured": False,
        "reachable": False,
        "mode": "demo",
        "detail": f"Unknown provider '{settings.ai_provider}'. Running in Demo Mode.",
    }

