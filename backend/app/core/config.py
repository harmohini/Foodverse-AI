"""FoodVerse AI Backend Configuration."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    app_name: str = "FoodVerse AI"
    app_env: str = "development"
    debug: bool = True
    version: str = "1.0.0"

    # AI Provider
    ai_provider: str = "demo"  # "openai" or "demo"
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
        return self.ai_provider == "demo" or not self.openai_api_key

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Ensure upload directory exists
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path("./data").mkdir(parents=True, exist_ok=True)
