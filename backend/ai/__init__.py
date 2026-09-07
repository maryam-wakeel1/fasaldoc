"""Provider selection is centralized here so routes stay provider-neutral."""

from backend.ai.base import AIProvider
from backend.ai.demo_provider import DemoProvider
from backend.ai.gemini_provider import GeminiProvider
from backend.ai.qwen_provider import QwenProvider
from backend.config import settings


def get_provider() -> AIProvider:
    if settings.ai_provider == "qwen":
        return QwenProvider()
    if settings.ai_provider == "gemini" or (settings.ai_provider == "auto" and settings.gemini_api_key):
        return GeminiProvider(settings.gemini_api_key)
    return DemoProvider()


__all__ = ["AIProvider", "get_provider"]
