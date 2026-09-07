"""Google AI Studio implementation for image, text, and speech tasks."""

from __future__ import annotations

import json
import mimetypes
import wave
from io import BytesIO
from pathlib import Path
from typing import Any

from backend.ai.base import AIProvider, UNCERTAIN_EXPLANATIONS
from backend.config import settings

_URDU_VOICE = "Kore"
_ENGLISH_VOICE = "Charon"


class GeminiProvider(AIProvider):
    provider_name = "gemini"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for the Gemini provider.")
        self.api_key = api_key

    def _client_and_types(self):
        try:
            from google import genai
            from google.genai import types
        except ImportError as error:
            raise RuntimeError("google-genai is not installed. Run pip install -r requirements.txt.") from error
        return genai.Client(api_key=self.api_key), types

    @staticmethod
    def _parse_json(response: Any) -> dict[str, Any]:
        text = getattr(response, "text", "") or ""
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise RuntimeError("Gemini returned an invalid structured diagnosis.") from error

    def _image_part(self, types: Any, image_path: str):
        path = Path(image_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        return types.Part.from_bytes(data=path.read_bytes(), mime_type=mime_type)

    def analyze_crop_photo(
        self, image_path: str, context: str, language: str = "ur"
    ) -> dict[str, Any]:
        client, types = self._client_and_types()
        is_english = (language or "ur").strip().lower() == "en"

        if is_english:
            prompt = f"""
You are a cautious crop-disease screening assistant for small and mid-scale farmers.
Inspect the supplied crop-leaf photo and use this local agriculture context when relevant:
{context or "No matching local record was found."}

Return JSON only with these keys:
- visual_symptoms_english: a brief plain-English description of visible symptoms
- suspected_crop: crop name if visible, otherwise an empty string
- raw_diagnosis: short internal diagnostic lead
- image_confidence: integer 0 through 100

Do not state certainty when the image is blurred, incomplete, or ambiguous.
""".strip()
        else:
            prompt = f"""
You are a cautious Pakistani crop-disease screening assistant. Inspect the supplied crop-leaf photo.
Use this local agriculture context when relevant:
{context or "No matching local record was found."}

Return JSON only with these keys:
- visual_symptoms_urdu: a brief Urdu description of visible symptoms
- suspected_crop: crop name if visible, otherwise an empty string
- raw_diagnosis: short English/Urdu internal diagnostic lead
- image_confidence: integer 0 through 100

Do not state certainty when the image is blurred, incomplete, or ambiguous.
""".strip()

        response = client.models.generate_content(
            model=settings.gemini_vision_model,
            contents=[prompt, self._image_part(types, image_path)],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return self._parse_json(response)

    def generate_advisory(
        self,
        diagnosis_data: dict[str, Any],
        user_question: str,
        knowledge_context: str,
        language: str = "ur",
    ) -> dict[str, Any]:
        client, types = self._client_and_types()
        is_english = (language or "ur").strip().lower() == "en"

        if is_english:
            prompt = f"""
You provide safe, practical crop advice for small and mid-scale farmers.
Write simple plain English in an empathetic, conversational style. Use the local knowledge below
as the primary source for crop-specific remedies; do not invent chemical rates or unsafe treatments.

Local knowledge:
{knowledge_context or "No local record matched."}

Photo analysis:
{json.dumps(diagnosis_data, ensure_ascii=False)}

Farmer question:
{user_question or "Guide me based on the leaf photo"}

Return JSON only with exactly these keys:
- diagnosis_english: concise English diagnosis name
- confidence_score: integer from 0 to 100
- treatment_plan_english: simple low-cost locally relevant treatment in English
- spoken_explanation_english: a short English response suitable for speech playback
- is_uncertain: boolean

If the image is unclear, evidence conflicts, or confidence is below 65, set is_uncertain to true,
keep confidence_score below 65, and use this exact spoken_explanation_english:
"{UNCERTAIN_EXPLANATIONS['en']}"
""".strip()
        else:
            prompt = f"""
You provide safe, practical crop advice for small and mid-scale farmers in Pakistan.
Write simple Urdu in an empathetic, conversational style. Use the local knowledge below as the
primary source for crop-specific remedies; do not invent chemical rates or unsafe treatments.

Local knowledge:
{knowledge_context or "No local record matched."}

Photo analysis:
{json.dumps(diagnosis_data, ensure_ascii=False)}

Farmer question:
{user_question or "تصویر دیکھ کر رہنمائی کریں"}

Return JSON only with exactly these keys:
- diagnosis_urdu: concise Urdu diagnosis name
- confidence_score: integer from 0 to 100
- treatment_plan_urdu: simple low-cost locally relevant treatment in Urdu
- spoken_explanation_urdu: a short Urdu response suitable for speech playback
- is_uncertain: boolean

If the image is unclear, evidence conflicts, or confidence is below 65, set is_uncertain to true,
keep confidence_score below 65, and use this exact spoken_explanation_urdu:
"{UNCERTAIN_EXPLANATIONS['ur']}"
""".strip()

        response = client.models.generate_content(
            model=settings.gemini_vision_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        return self._parse_json(response)

    def speech_to_text(self, audio_path: str, language: str = "ur") -> str:
        client, types = self._client_and_types()
        is_english = (language or "ur").strip().lower() == "en"
        path = Path(audio_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "audio/webm"
        prompt = (
            "Transcribe this farmer's voice message in English. Return only the English transcript."
            if is_english
            else "Transcribe this farmer's voice message in Urdu. Return only the Urdu transcript."
        )
        response = client.models.generate_content(
            model=settings.gemini_vision_model,
            contents=[prompt, types.Part.from_bytes(data=path.read_bytes(), mime_type=mime_type)],
        )
        return (getattr(response, "text", "") or "").strip()

    def text_to_speech(self, text: str, language: str = "ur") -> bytes:
        client, types = self._client_and_types()
        is_english = (language or "ur").strip().lower() == "en"
        voice_name = _ENGLISH_VOICE if is_english else _URDU_VOICE
        try:
            speech_config = types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            )
            response = client.models.generate_content(
                model=settings.gemini_tts_model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"], speech_config=speech_config
                ),
            )
            audio_data = response.candidates[0].content.parts[0].inline_data.data
        except (AttributeError, IndexError, TypeError) as error:
            raise RuntimeError("Gemini TTS did not return audio data.") from error

        if audio_data[:4] == b"RIFF":
            return audio_data
        return self._pcm_to_wav(audio_data)

    @staticmethod
    def _pcm_to_wav(pcm_data: bytes) -> bytes:
        output = BytesIO()
        with wave.open(output, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(24_000)
            audio.writeframes(pcm_data)
        return output.getvalue()
