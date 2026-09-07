"""Future Alibaba Cloud Model Studio / Qwen implementation boundary."""

from __future__ import annotations

from typing import Any

from backend.ai.base import AIProvider


class QwenProvider(AIProvider):
    provider_name = "qwen"

    def _unavailable(self) -> None:
        raise NotImplementedError("Qwen integration is not configured yet. Use Gemini or demo mode.")

    def analyze_crop_photo(
        self, image_path: str, context: str, language: str = "ur"
    ) -> dict[str, Any]:
        self._unavailable()

    def generate_advisory(
        self,
        diagnosis_data: dict[str, Any],
        user_question: str,
        knowledge_context: str,
        language: str = "ur",
    ) -> dict[str, Any]:
        self._unavailable()

    def speech_to_text(self, audio_path: str, language: str = "ur") -> str:
        self._unavailable()

    def text_to_speech(self, text: str, language: str = "ur") -> bytes:
        self._unavailable()
