"""Provider boundary and response safety rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

UNCERTAIN_EXPLANATIONS = {
    "ur": "مجھے پورا یقین نہیں ہے۔ براہ کرم قریبی زرعی ماہر سے تصدیق کروائیں۔",
    "en": "I am not fully certain. Please confirm with a local agriculture expert.",
}

UNCERTAIN_EXPLANATION = UNCERTAIN_EXPLANATIONS["ur"]


def _as_language(value: str | None) -> str:
    candidate = (value or "").strip().lower()
    return candidate if candidate in UNCERTAIN_EXPLANATIONS else "ur"


class AIProvider(ABC):
    provider_name = "base"
    is_demo = False

    @abstractmethod
    def analyze_crop_photo(
        self, image_path: str, context: str, language: str = "ur"
    ) -> dict[str, Any]:
        """Return visual symptoms and the initial image-based diagnosis."""

    @abstractmethod
    def generate_advisory(
        self,
        diagnosis_data: dict[str, Any],
        user_question: str,
        knowledge_context: str,
        language: str = "ur",
    ) -> dict[str, Any]:
        """Return the farmer-facing structured advisory in the requested language."""

    def generate_urdu_advisory(
        self,
        diagnosis_data: dict[str, Any],
        user_question: str,
        knowledge_context: str,
    ) -> dict[str, Any]:
        """Backward-compatible wrapper that delegates to generate_advisory(language='ur')."""
        return self.generate_advisory(diagnosis_data, user_question, knowledge_context, language="ur")

    @abstractmethod
    def speech_to_text(self, audio_path: str, language: str = "ur") -> str:
        """Transcribe a voice question in the requested language."""

    @abstractmethod
    def text_to_speech(self, text: str, language: str = "ur") -> bytes:
        """Return a browser-playable audio file for the response."""


def normalize_advisory(raw: dict[str, Any], language: str = "ur") -> dict[str, Any]:
    """Constrain model output to the response contract used by routes and UI.

    Always emits both *_urdu and *_english keys so history stays readable in either
    language; the frontend picks the active-language keys.
    """
    language = _as_language(language)
    try:
        confidence = int(float(raw.get("confidence_score", 0)))
    except (TypeError, ValueError):
        confidence = 0
    confidence = max(0, min(100, confidence))

    uncertain = bool(raw.get("is_uncertain", False)) or confidence < 65
    uncertain_urdu = UNCERTAIN_EXPLANATIONS["ur"]
    uncertain_english = UNCERTAIN_EXPLANATIONS["en"]

    urdu_diagnosis = str(
        raw.get("diagnosis_urdu") or raw.get("diagnosis_english") or "تشخیص واضح نہیں ہے"
    ).strip()
    urdu_treatment = str(
        raw.get("treatment_plan_urdu") or raw.get("treatment_plan_english")
        or "قریبی زرعی ماہر سے مشورہ کریں۔"
    ).strip()
    urdu_spoken = str(raw.get("spoken_explanation_urdu") or "").strip()
    english_diagnosis = str(
        raw.get("diagnosis_english") or raw.get("diagnosis_urdu") or "Diagnosis is not clear."
    ).strip()
    english_treatment = str(
        raw.get("treatment_plan_english") or raw.get("treatment_plan_urdu")
        or "Please consult a local agriculture expert."
    ).strip()
    english_spoken = str(raw.get("spoken_explanation_english") or "").strip()

    if uncertain:
        urdu_spoken = uncertain_urdu
        english_spoken = uncertain_english

    return {
        "diagnosis_urdu": urdu_diagnosis or "تشخیص واضح نہیں ہے",
        "treatment_plan_urdu": urdu_treatment or "قریبی زرعی ماہر سے مشورہ کریں۔",
        "spoken_explanation_urdu": urdu_spoken or uncertain_urdu,
        "diagnosis_english": english_diagnosis or "Diagnosis is not clear.",
        "treatment_plan_english": english_treatment or "Please consult a local agriculture expert.",
        "spoken_explanation_english": english_spoken or uncertain_english,
        "confidence_score": confidence,
        "is_uncertain": uncertain,
        "language": language,
    }
