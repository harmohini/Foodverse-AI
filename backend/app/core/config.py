"""FoodVerse AI Backend Configuration."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App
    app_name: str = "FoodVerse AI"
    app_env: str = "development"
    debug: bool = True
    version: str = "1.0.0"

    # AI Provider: "gemini" (primary), "openai" (fallback), "demo"
    ai_provider: str = "gemini"

    # Google Gemini API (Primary AI provider)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_vision_model: str = "gemini-3.8-flash"
    gemini_text_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: float = 90.0
    gemini_connect_timeout_seconds: float = 10.0

    # OpenAI-compatible API (Optional fallback provider)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_vision_model: str = "gpt-4o"
    openai_text_model: str = "gpt-4o"

    # Database
    database_url: str = "sqlite:///./data/foodverse.db"

    # Upload limits
    max_image_size_mb: int = 10
    max_video_size_mb: int = 100
    max_audio_size_mb: int = 25
    max_video_duration_seconds: int = 300
    upload_dir: str = "./data/uploads"

    # CORS
    frontend_url: str = "http://localhost:5173"

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    @property
    def max_video_size_bytes(self) -> int:
        return self.max_video_size_mb * 1024 * 1024

    @property
    def max_audio_size_bytes(self) -> int:
        return self.max_audio_size_mb * 1024 * 1024

    @property
    def is_demo_mode(self) -> bool:
        return self.ai_provider == "demo"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url.startswith("sqlite:///./"):
            rel_part = self.database_url[len("sqlite:///./"):]
            abs_path = (BACKEND_DIR / rel_part).resolve()
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{abs_path}"
        return self.database_url

    @property
    def resolved_upload_dir(self) -> Path:
        p = Path(self.upload_dir)
        if not p.is_absolute():
            p = (BACKEND_DIR / p).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    model_config = {"env_file": str(BACKEND_DIR / ".env"), "extra": "ignore"}


settings = Settings()

# Ensure upload and data directories exist
settings.resolved_upload_dir.mkdir(parents=True, exist_ok=True)
