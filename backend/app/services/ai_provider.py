"""AI provider abstraction layer."""
from __future__ import annotations
import json
from typing import Any, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


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
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        # Determine image mime type
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

    async def generate_text(self, prompt: str, system: str = "") -> str:
        client = self._get_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = await client.chat.completions.create(
            model=settings.openai_text_model,
            messages=messages,
            max_tokens=2000,
            timeout=45.0,
        )
        return response.choices[0].message.content or ""


def get_provider() -> AIProvider:
    """Return the configured AI provider, falling back to demo if unavailable."""
    if settings.is_demo_mode:
        logger.info("Using DemoProvider (demo mode active)")
        return DemoProvider()
    if settings.ai_provider == "openai":
        logger.info("Using OpenAIProvider")
        return OpenAIProvider()
    logger.warning("Unknown provider config — falling back to DemoProvider")
    return DemoProvider()
