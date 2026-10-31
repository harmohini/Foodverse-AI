"""Health check endpoints."""
from fastapi import APIRouter
from app.schemas.schemas import HealthResponse
from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai_provider import redact_secrets

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
    if settings.is_demo_mode or settings.ai_provider == "demo":
        return {
            "provider": "demo",
            "configured": False,
            "reachable": False,
            "mode": "demo",
            "detail": "Running in Demo Mode. No AI provider is configured.",
        }

    if settings.ai_provider == "gemini":
        key = settings.gemini_api_key.strip() if settings.gemini_api_key else ""
        if not key or key in ("your_gemini_api_key_here", "AIza..."):
            return {
                "provider": "gemini",
                "configured": False,
                "reachable": False,
                "mode": "demo",
                "detail": "GEMINI_API_KEY is not configured. Running in Demo Mode.",
            }
        # Attempt a minimal API call to verify reachability
        try:
            from google import genai
            from google.genai import types
            import httpx

            connect_timeout_s = float(settings.gemini_connect_timeout_seconds)
            health_timeout_ms = int(connect_timeout_s * 1000)
            client_timeout = httpx.Timeout(
                timeout=connect_timeout_s,
                connect=connect_timeout_s,
                read=connect_timeout_s,
                write=connect_timeout_s,
            )
            http_opts = types.HttpOptions(
                timeout=health_timeout_ms,
                client_args={"timeout": client_timeout},
                async_client_args={"timeout": client_timeout},
            )
            client = genai.Client(api_key=key, http_options=http_opts)
            # Lightweight reachability check: retrieve model metadata without consuming tokens
            models_to_check = [settings.gemini_model, "gemini-flash-lite-latest"]
            active_model = settings.gemini_model
            last_exc = None
            for cand in models_to_check:
                try:
                    await client.aio.models.get(model=cand)
                    active_model = cand
                    last_exc = None
                    break
                except Exception as cand_exc:
                    last_exc = cand_exc
            if last_exc is not None:
                raise last_exc
            return {
                "provider": "gemini",
                "configured": True,
                "reachable": True,
                "mode": "live",
                "model": active_model,
                "detail": "Google Gemini API is reachable and responding.",
            }
        except Exception as exc:
            err_msg = redact_secrets(str(exc))
            logger.warning(f"Gemini connectivity check failed: {err_msg}")
            return {
                "provider": "gemini",
                "configured": True,
                "reachable": False,
                "mode": "degraded",
                "detail": f"Gemini API key is set but the API did not respond: {type(exc).__name__}",
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
            err_msg = redact_secrets(str(exc))
            logger.warning(f"Provider connectivity check failed: {err_msg}")
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

