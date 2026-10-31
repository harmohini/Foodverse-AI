"""AI provider abstraction layer with robust error handling and secret redaction."""
from __future__ import annotations
import re
import json
from typing import Any, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ─── Exceptions ────────────────────────────────────────────────────────────

class AIProviderError(Exception):
    """Base exception for AI provider failures."""

    def __init__(self, message: str, status_code: int = 502, code: str = "provider_error"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class AIAuthenticationError(AIProviderError):
    def __init__(
        self,
        message: str = (
            "OpenAI API authentication failed: Invalid or missing API key. "
            "Please verify OPENAI_API_KEY in backend/.env, or switch to AI_PROVIDER=demo."
        ),
    ):
        super().__init__(message, status_code=502, code="authentication_error")


class AIRateLimitError(AIProviderError):
    def __init__(
        self,
        message: str = (
            "OpenAI rate limit or credit quota exceeded. "
            "Please check your OpenAI account billing or switch to AI_PROVIDER=demo."
        ),
    ):
        super().__init__(message, status_code=502, code="rate_limit_error")


class AIConnectionError(AIProviderError):
    def __init__(
        self,
        message: str = (
            "Unable to connect to the AI provider endpoint. "
            "Please check network connectivity or switch to AI_PROVIDER=demo."
        ),
    ):
        super().__init__(message, status_code=503, code="connection_error")


class AIServiceUnavailableError(AIProviderError):
    def __init__(
        self,
        message: str = (
            "Google Gemini API is currently experiencing temporary high demand (503 Service Unavailable). "
            "Please try again in a few moments, or switch to AI_PROVIDER=demo."
        ),
    ):
        super().__init__(message, status_code=503, code="service_unavailable")


class AIResponseFormatError(AIProviderError):
    def __init__(
        self,
        message: str = "The AI provider returned an unparseable response. Please retry.",
    ):
        super().__init__(message, status_code=502, code="response_format_error")


def redact_secrets(text: str) -> str:
    """Ensure no API keys or secret tokens appear in log or error text."""
    if not text:
        return text
    if settings.openai_api_key and len(settings.openai_api_key) > 5:
        text = text.replace(settings.openai_api_key, "[REDACTED_API_KEY]")
    if settings.gemini_api_key and len(settings.gemini_api_key) > 5:
        text = text.replace(settings.gemini_api_key, "[REDACTED_API_KEY]")
    # Redact any sk-... patterns
    text = re.sub(r"sk-[A-Za-z0-9_\-]{15,}", "[REDACTED_KEY]", text)
    # Redact any AIza... patterns
    text = re.sub(r"AIza[A-Za-z0-9_\-]{30,}", "[REDACTED_KEY]", text)
    return text


def _handle_gemini_error(exc: Exception) -> AIProviderError:
    """Map Google Gemini exceptions to structured AIProviderError instances."""
    import httpx
    msg = redact_secrets(str(exc))
    exc_type = type(exc).__name__
    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)

    msg_lower = msg.lower()
    if (
        status in (401, 403)
        or (status == 400 and any(w in msg_lower for w in ("api_key", "api key", "invalid", "unauthenticated")))
        or "api_key_invalid" in msg_lower
        or "api key not valid" in msg_lower
        or "unauthenticated" in msg_lower
        or "permission_denied" in msg_lower
        or "permissiondenied" in exc_type.lower()
        or "authentication" in exc_type.lower()
    ):
        return AIAuthenticationError(
            "Google Gemini API authentication failed: Invalid or missing API key. "
            "Please check GEMINI_API_KEY in backend/.env, or switch to AI_PROVIDER=demo."
        )

    if (
        status == 429
        or "resource_exhausted" in msg_lower
        or "quota" in msg_lower
        or "rate limit" in msg_lower
        or "ratelimit" in exc_type.lower()
    ):
        return AIRateLimitError(
            "Google Gemini API rate limit or credit quota exceeded. "
            "Please check your Google AI Studio quota and billing, or switch to AI_PROVIDER=demo."
        )

    # Check for timeout errors in message, exception type, or class hierarchy
    is_timeout = (
        "timeout" in msg_lower
        or "timed out" in msg_lower
        or "timeout" in exc_type.lower()
        or any("timeout" in t.__name__.lower() for t in type(exc).__mro__)
        or isinstance(exc, (TimeoutError, httpx.TimeoutException))
        or status in (408, 504)
    )
    if is_timeout:
        return AIConnectionError(
            "Google Gemini API request timed out. Please try again or switch to AI_PROVIDER=demo."
        )

    if (
        status == 503
        or "high demand" in msg_lower
        or "spikes in demand" in msg_lower
        or "unavailable" in msg_lower
        or "service unavailable" in msg_lower
    ):
        return AIServiceUnavailableError(
            "Google Gemini API is currently experiencing temporary high demand (503 Service Unavailable). "
            "Please try again in a moment, or switch to AI_PROVIDER=demo."
        )

    is_connection = (
        "connection" in msg_lower
        or "connect" in exc_type.lower()
        or "network" in msg_lower
        or "unreachable" in msg_lower
        or any("connect" in t.__name__.lower() or "network" in t.__name__.lower() for t in type(exc).__mro__)
        or isinstance(exc, (ConnectionError, httpx.NetworkError))
    )
    if is_connection:
        return AIConnectionError(
            "Could not connect to Google Gemini API endpoint. Please check network connectivity or switch to AI_PROVIDER=demo."
        )

    return AIProviderError(f"Google Gemini API error: {msg}")


def _handle_openai_error(exc: Exception) -> AIProviderError:
    """Map external exceptions to structured AIProviderError instances."""
    msg = redact_secrets(str(exc))
    exc_type = type(exc).__name__
    status = getattr(exc, "status_code", None)

    if "401" in msg or "AuthenticationError" in exc_type or status == 401:
        return AIAuthenticationError(
            "OpenAI API authentication failed: Invalid or unauthorized API key. "
            "Please check OPENAI_API_KEY in backend/.env, or switch to AI_PROVIDER=demo."
        )
    if "403" in msg or "PermissionDeniedError" in exc_type or status == 403:
        return AIAuthenticationError(
            "OpenAI API access denied (403 Forbidden). "
            "Please verify your API key permissions and network policy, or switch to AI_PROVIDER=demo."
        )
    if "429" in msg or "RateLimitError" in exc_type or status == 429:
        return AIRateLimitError(
            "OpenAI rate limit or credit quota exceeded. "
            "Please check your OpenAI account balance or switch to AI_PROVIDER=demo."
        )
    if "timeout" in msg.lower() or "APITimeoutError" in exc_type:
        return AIConnectionError(
            "OpenAI API request timed out. Please try again or switch to AI_PROVIDER=demo."
        )
    if "connection" in msg.lower() or "APIConnectionError" in exc_type:
        return AIConnectionError(
            "Could not connect to OpenAI API endpoint. Please check network connectivity or switch to AI_PROVIDER=demo."
        )
    return AIProviderError(f"AI Provider error: {msg}")


# ─── Providers ─────────────────────────────────────────────────────────────

class AIProvider:
    """Base AI provider interface."""

    @property
    def name(self) -> str:
        return "base"

    @property
    def is_demo(self) -> bool:
        return True

    async def analyze_image(self, image_path: str, prompt: str) -> str:
        raise NotImplementedError

    async def generate_text(self, prompt: str, system: str = "") -> str:
        raise NotImplementedError


class DemoProvider(AIProvider):
    """Deterministic demo provider — no external calls."""

    @property
    def name(self) -> str:
        return "demo"

    @property
    def is_demo(self) -> bool:
        return True

    async def analyze_image(self, image_path: str, prompt: str) -> str:
        logger.info("DemoProvider: returning demo image analysis (no real inference)")
        return "DEMO_IMAGE_ANALYSIS"

    async def generate_text(self, prompt: str, system: str = "") -> str:
        logger.info("DemoProvider: returning demo text generation (no real inference)")
        return "DEMO_TEXT_GENERATION"


class OpenAIProvider(AIProvider):
    """OpenAI / OpenAI-compatible vision + text provider."""

    def __init__(self):
        self._client = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def is_demo(self) -> bool:
        return False

    def _get_client(self):
        if not settings.openai_api_key or settings.openai_api_key.strip() in ("", "sk-...", "your_openai_api_key_here"):
            raise AIAuthenticationError(
                "OPENAI_API_KEY is not configured. Please add a valid key in backend/.env "
                "or switch AI_PROVIDER=demo to use Demo Mode."
            )
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return self._client

    async def analyze_image(self, image_path: str, prompt: str) -> str:
        import base64
        client = self._get_client()
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            ext = image_path.rsplit(".", 1)[-1].lower()
            mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
            response = await client.chat.completions.create(
                model=settings.openai_vision_model,
                messages=[
                    {"role": "system", "content": "You are FoodVerse AI, a helpful food analysis assistant. Provide structured, accurate, and helpful food information. Always clarify when results are estimates."},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}},
                        {"type": "text", "text": prompt},
                    ]},
                ],
                max_tokens=1500,
                timeout=30.0,
            )
            return response.choices[0].message.content or ""
        except AIProviderError:
            raise
        except Exception as exc:
            err = _handle_openai_error(exc)
            logger.error(f"OpenAI vision call failed: {err.message}")
            raise err from None

    async def generate_text(self, prompt: str, system: str = "") -> str:
        client = self._get_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        try:
            response = await client.chat.completions.create(
                model=settings.openai_text_model,
                messages=messages,
                max_tokens=2000,
                timeout=45.0,
            )
            return response.choices[0].message.content or ""
        except AIProviderError:
            raise
        except Exception as exc:
            err = _handle_openai_error(exc)
            logger.error(f"OpenAI text call failed: {err.message}")
            raise err from None


class GeminiProvider(AIProvider):
    """Google Gemini vision + text provider using the official Google Gen AI SDK."""

    def __init__(self):
        self._client = None

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def is_demo(self) -> bool:
        return False

    def _get_client(self):
        key = settings.gemini_api_key.strip() if settings.gemini_api_key else ""
        if not key or key in ("", "your_gemini_api_key_here", "AIza..."):
            raise AIAuthenticationError(
                "GEMINI_API_KEY is not configured. Please add a valid key in backend/.env "
                "or switch AI_PROVIDER=demo to use Demo Mode."
            )
        if self._client is None:
            from google import genai
            from google.genai import types
            import httpx

            overall_timeout_s = float(settings.gemini_timeout_seconds)
            connect_timeout_s = float(settings.gemini_connect_timeout_seconds)
            # HttpOptions.timeout is in milliseconds in the Google GenAI Python SDK
            overall_timeout_ms = int(overall_timeout_s * 1000)

            client_timeout = httpx.Timeout(
                timeout=overall_timeout_s,
                connect=connect_timeout_s,
                read=overall_timeout_s,
                write=overall_timeout_s,
            )

            http_opts = types.HttpOptions(
                timeout=overall_timeout_ms,
                client_args={"timeout": client_timeout},
                async_client_args={"timeout": client_timeout},
            )
            self._client = genai.Client(api_key=key, http_options=http_opts)
        return self._client

    def _get_model_candidates(self, primary: str) -> list[str]:
        candidates = [primary]
        for fallback in ("gemini-flash-lite-latest", "gemini-flash-latest"):
            if fallback not in candidates:
                candidates.append(fallback)
        return candidates

    async def analyze_image(self, image_path: str, prompt: str) -> str:
        client = self._get_client()
        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            import mimetypes
            guessed_mime, _ = mimetypes.guess_type(image_path)
            ext = image_path.rsplit(".", 1)[-1].lower()
            mime = guessed_mime or {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
                "gif": "image/gif",
            }.get(ext, "image/jpeg")

            from google.genai import types
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime)
            timeout_ms = int(settings.gemini_timeout_seconds * 1000)
            config = types.GenerateContentConfig(
                system_instruction=(
                    "You are FoodVerse AI, a helpful food analysis assistant. "
                    "Provide structured, accurate, and helpful food information. "
                    "Always clarify when results are estimates."
                ),
                http_options=types.HttpOptions(timeout=timeout_ms),
            )
            models_to_try = self._get_model_candidates(settings.gemini_vision_model)
            last_exc = None
            for model_name in models_to_try:
                try:
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=[image_part, prompt],
                        config=config,
                    )
                    return response.text or ""
                except Exception as exc:
                    last_exc = exc
                    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                    if status in (503, 404, 429) or "high demand" in str(exc).lower():
                        logger.warning(
                            f"Gemini model '{model_name}' encountered {status or type(exc).__name__}. "
                            "Retrying with fallback model..."
                        )
                        continue
                    raise exc
            if last_exc:
                raise last_exc
            return ""
        except AIProviderError:
            raise
        except Exception as exc:
            err = _handle_gemini_error(exc)
            logger.error(
                f"Gemini vision call failed: {type(exc).__name__}: {err.message} "
                f"(details: {redact_secrets(str(exc))})"
            )
            raise err from None

    async def generate_text(self, prompt: str, system: str = "") -> str:
        client = self._get_client()
        try:
            from google.genai import types
            timeout_ms = int(settings.gemini_timeout_seconds * 1000)
            config = types.GenerateContentConfig(
                system_instruction=system if system else None,
                http_options=types.HttpOptions(timeout=timeout_ms),
            )
            models_to_try = self._get_model_candidates(settings.gemini_text_model)
            last_exc = None
            for model_name in models_to_try:
                try:
                    response = await client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config,
                    )
                    return response.text or ""
                except Exception as exc:
                    last_exc = exc
                    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                    if status in (503, 404, 429) or "high demand" in str(exc).lower():
                        logger.warning(
                            f"Gemini model '{model_name}' encountered {status or type(exc).__name__}. "
                            "Retrying with fallback model..."
                        )
                        continue
                    raise exc
            if last_exc:
                raise last_exc
            return ""
        except AIProviderError:
            raise
        except Exception as exc:
            err = _handle_gemini_error(exc)
            logger.error(
                f"Gemini text call failed: {type(exc).__name__}: {err.message} "
                f"(details: {redact_secrets(str(exc))})"
            )
            raise err from None


def get_provider() -> AIProvider:
    """Return the configured AI provider, preserving provider selection without silent switching."""
    if settings.is_demo_mode:
        logger.info("Using DemoProvider (demo mode active)")
        return DemoProvider()
    if settings.ai_provider == "gemini":
        logger.info("Using GeminiProvider")
        return GeminiProvider()
    if settings.ai_provider == "openai":
        logger.info("Using OpenAIProvider")
        return OpenAIProvider()
    logger.warning(f"Unknown provider config '{settings.ai_provider}' — falling back to DemoProvider")
    return DemoProvider()
