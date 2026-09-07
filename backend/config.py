"""Application settings and filesystem locations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    base_dir: Path = BASE_DIR
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    ai_provider: str = os.getenv("AI_PROVIDER", "auto").strip().lower()
    gemini_vision_model: str = os.getenv("GEMINI_VISION_MODEL", "gemini-3.6-flash")
    gemini_tts_model: str = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8000"))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
        if origin.strip()
    ) or ("*",)

    @property
    def storage_dir(self) -> Path:
        return self.base_dir / "storage"

    @property
    def uploads_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def audio_dir(self) -> Path:
        return self.storage_dir / "audio"

    @property
    def database_path(self) -> Path:
        return self.base_dir / "backend" / "database.db"

    @property
    def frontend_dir(self) -> Path:
        return self.base_dir / "frontend"


settings = Settings()
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_LANGUAGES = ("ur", "en")
DEFAULT_LANGUAGE = "ur"

URDU_FALLBACK_QUESTION = "تصویر دیکھ کر رہنمائی کریں"
ENGLISH_FALLBACK_QUESTION = "Guide me based on the leaf photo"
