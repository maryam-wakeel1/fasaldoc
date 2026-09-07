"""Clearly labelled local demo provider used when no API key is configured."""

from __future__ import annotations

import hashlib
import math
import wave
from io import BytesIO
from pathlib import Path
from typing import Any

from backend.ai.base import AIProvider, UNCERTAIN_EXPLANATIONS

_DEMO_CASES = {
    "ur": [
        {
            "diagnosis_urdu": "پتوں کا زنگ (نمونہ)",
            "treatment_plan_urdu": "یہ صرف نمونہ ہے۔ اصل استعمال سے پہلے قریبی زرعی ماہر سے پتے دکھا کر تصدیق کریں۔",
            "visual_symptoms_urdu": "نمونے کے طور پر پتوں پر بھورے دھبے دکھائے گئے ہیں۔",
        },
        {
            "diagnosis_urdu": "پتوں کا جھلساؤ (نمونہ)",
            "treatment_plan_urdu": "یہ صرف نمونہ ہے۔ آبپاشی اور کھاد کا مقامی ماہر سے جائزہ کروائیں۔",
            "visual_symptoms_urdu": "نمونے کے طور پر پتوں کے کنارے خشک دکھائے گئے ہیں۔",
        },
        {
            "diagnosis_urdu": "سفید مکھی کا اثر (نمونہ)",
            "treatment_plan_urdu": "یہ صرف نمونہ ہے۔ فصل کا معائنہ کروا کر مقامی، منظور شدہ علاج استعمال کریں۔",
            "visual_symptoms_urdu": "نمونے کے طور پر پتے پیلے اور مڑے ہوئے دکھائے گئے ہیں۔",
        },
    ],
    "en": [
        {
            "diagnosis_english": "Leaf Rust (demo)",
            "treatment_plan_english": "This is only a demo. Before real use, show the leaves to a local agriculture expert for confirmation.",
            "visual_symptoms_english": "Brown spots on leaves are shown as an example.",
        },
        {
            "diagnosis_english": "Leaf Blight (demo)",
            "treatment_plan_english": "This is only a demo. Have irrigation and fertilizer reviewed by a local expert.",
            "visual_symptoms_english": "Dry leaf edges are shown as an example.",
        },
        {
            "diagnosis_english": "Whitefly Impact (demo)",
            "treatment_plan_english": "This is only a demo. Inspect the crop and only use locally approved treatments.",
            "visual_symptoms_english": "Yellowing and curling leaves are shown as an example.",
        },
    ],
}


class DemoProvider(AIProvider):
    provider_name = "demo"
    is_demo = True

    def _case_for(self, image_path: str, language: str) -> dict[str, Any]:
        cases = _DEMO_CASES.get(language, _DEMO_CASES["ur"])
        file_hash = hashlib.sha256(Path(image_path).read_bytes()).digest()
        return cases[file_hash[0] % len(cases)]

    def analyze_crop_photo(
        self, image_path: str, context: str, language: str = "ur"
    ) -> dict[str, Any]:
        case = self._case_for(image_path, language)
        return {**case, "raw_diagnosis": "No Gemini key configured; deterministic demo response."}

    def generate_advisory(
        self,
        diagnosis_data: dict[str, Any],
        user_question: str,
        knowledge_context: str,
        language: str = "ur",
    ) -> dict[str, Any]:
        is_english = (language or "ur").strip().lower() == "en"
        if is_english:
            return {
                "diagnosis_english": diagnosis_data.get("diagnosis_english") or "Leaf issue (demo)",
                "confidence_score": 45,
                "treatment_plan_english": diagnosis_data.get("treatment_plan_english")
                or "This is a demo; please consult an agriculture expert.",
                "spoken_explanation_english": "This is only a demo. For a real diagnosis, please consult an agriculture expert.",
                "is_uncertain": True,
            }
        return {
            "diagnosis_urdu": diagnosis_data.get("diagnosis_urdu") or "تشخیص (نمونہ)",
            "confidence_score": 45,
            "treatment_plan_urdu": diagnosis_data.get("treatment_plan_urdu")
            or "یہ صرف نمونہ ہے، اصل تشخیص کے لیے زرعی ماہر سے رابطہ کریں۔",
            "spoken_explanation_urdu": "یہ صرف نمونہ ہے، اصل تشخیص کے لیے زرعی ماہر سے رابطہ کریں۔",
            "is_uncertain": True,
        }

    def speech_to_text(self, audio_path: str, language: str = "ur") -> str:
        return ""

    def text_to_speech(self, text: str, language: str = "ur") -> bytes:
        sample_rate = 24_000
        duration_seconds = 1.2
        frames = bytearray()
        for index in range(int(sample_rate * duration_seconds)):
            amplitude = int(2600 * math.sin(2 * math.pi * 440 * index / sample_rate))
            frames.extend(amplitude.to_bytes(2, byteorder="little", signed=True))

        output = BytesIO()
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(sample_rate)
            audio.writeframes(bytes(frames))
        return output.getvalue()
