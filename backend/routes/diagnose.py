"""Diagnosis endpoint: uploads, grounding, AI orchestration, and persistence."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.ai import get_provider
from backend.ai.base import normalize_advisory
from backend.config import (
    ALLOWED_IMAGE_TYPES,
    DEFAULT_LANGUAGE,
    ENGLISH_FALLBACK_QUESTION,
    SUPPORTED_LANGUAGES,
    URDU_FALLBACK_QUESTION,
    settings,
)
from backend.data.data_loader import (
    get_relevant_knowledge,
    get_relevant_records,
    resolve_reference_images,
)
from backend.database import save_session

router = APIRouter(prefix="/api", tags=["diagnosis"])
logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

_MESSAGES = {
    "ur": {
        "missing_image": "پہلے فصل کے پتے کی تصویر منتخب کریں۔",
        "bad_image_type": "براہ کرم JPG، PNG یا WEBP فصل کی تصویر منتخب کریں۔",
        "image_too_large": "تصویر بہت بڑی ہے۔ 10 MB سے چھوٹی تصویر منتخب کریں۔",
        "bad_image_bytes": "منتخب فائل فصل کی درست تصویر نہیں لگتی۔",
        "audio_too_large": "آواز کی فائل بہت بڑی ہے۔ مختصر پیغام دوبارہ ریکارڈ کریں۔",
        "transcript_failed": "آواز کا متن نہیں بن سکا؛ تصویر سے رہنمائی جاری رکھی گئی ہے۔",
        "service_unavailable": "تشخیص سروس ابھی دستیاب نہیں ہے۔ براہ کرم کچھ دیر بعد دوبارہ کوشش کریں۔",
        "tts_failed": "آواز تیار نہیں ہو سکی، براہ کرم نیچے دیا گیا متن پڑھیں۔",
        "audio_notice_missing": "آواز کا متن نہیں بن سکا؛ تصویر سے رہنمائی جاری رکھی گئی ہے۔",
        "audio_unavailable": "آواز دستیاب نہیں، اوپر دیا گیا جواب پڑھیں۔",
    },
    "en": {
        "missing_image": "Please select a crop leaf image first.",
        "bad_image_type": "Please choose a JPG, PNG, or WEBP crop image.",
        "image_too_large": "Image is too large. Please choose one smaller than 10 MB.",
        "bad_image_bytes": "The selected file does not appear to be a valid crop image.",
        "audio_too_large": "Audio is too large. Please record a shorter message.",
        "transcript_failed": "Could not transcribe the audio; continuing with the image.",
        "service_unavailable": "Diagnosis service is unavailable right now. Please try again shortly.",
        "tts_failed": "Could not prepare audio. Please read the text below.",
        "audio_notice_missing": "Could not transcribe the audio; continuing with the image.",
        "audio_unavailable": "Audio is not available. Please read the answer above.",
    },
}


def _resolve_language(raw: str | None) -> str:
    candidate = (raw or "").strip().lower()
    return candidate if candidate in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def _local(language: str, key: str) -> str:
    return _MESSAGES.get(language, _MESSAGES[DEFAULT_LANGUAGE]).get(
        key, _MESSAGES[DEFAULT_LANGUAGE][key]
    )


def _bad_request(language: str, key: str, http_status: int) -> None:
    raise HTTPException(
        status_code=http_status,
        detail={"message_urdu": _local("ur", key), "message_english": _local("en", key), "language": language},
    )


def _is_image_bytes(content_type: str, content: bytes) -> bool:
    signatures = {
        "image/jpeg": content.startswith(b"\xff\xd8\xff"),
        "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": content[:4] == b"RIFF" and content[8:12] == b"WEBP",
    }
    return signatures.get(content_type, False)


def _media_url(path: Path) -> str:
    return f"/media/{path.relative_to(settings.storage_dir).as_posix()}"


@router.post("/diagnose")
async def diagnose_crop(
    image: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    text_question: str | None = Form(None),
    language: str = Form(DEFAULT_LANGUAGE),
) -> dict:
    resolved_language = _resolve_language(language)
    fallback_question = (
        ENGLISH_FALLBACK_QUESTION if resolved_language == "en" else URDU_FALLBACK_QUESTION
    )

    if image is None:
        _bad_request(resolved_language, "missing_image", status.HTTP_400_BAD_REQUEST)

    content_type = (image.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        _bad_request(resolved_language, "bad_image_type", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    image_bytes = await image.read(settings.max_upload_bytes + 1)
    if len(image_bytes) > settings.max_upload_bytes:
        _bad_request(resolved_language, "image_too_large", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    if not _is_image_bytes(content_type, image_bytes):
        _bad_request(resolved_language, "bad_image_bytes", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    session_id = str(uuid4())
    upload_dir = settings.uploads_dir / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    image_path = upload_dir / f"leaf{_IMAGE_EXTENSIONS[content_type]}"
    image_path.write_bytes(image_bytes)

    audio_path: Path | None = None
    if audio:
        audio_bytes = await audio.read(settings.max_upload_bytes + 1)
        if len(audio_bytes) > settings.max_upload_bytes:
            _bad_request(resolved_language, "audio_too_large", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        if audio_bytes:
            extension = Path(audio.filename or "voice.webm").suffix.lower()
            extension = extension if extension and len(extension) <= 8 else ".webm"
            audio_path = upload_dir / f"question{extension}"
            audio_path.write_bytes(audio_bytes)

    provider = get_provider()
    transcript: str | None = None
    audio_notice: str | None = None
    if audio_path:
        try:
            transcript = provider.speech_to_text(str(audio_path), language=resolved_language) or None
            if not transcript:
                audio_notice = _local(resolved_language, "audio_notice_missing")
        except Exception:
            logger.exception("Speech transcription failed for session %s", session_id)
            audio_notice = _local(resolved_language, "audio_notice_missing")

    question = (text_question or transcript or fallback_question).strip()[:1_000]
    knowledge_context = get_relevant_knowledge(question, language=resolved_language)

    try:
        visual_diagnosis = provider.analyze_crop_photo(
            str(image_path), knowledge_context, language=resolved_language
        )
        if not isinstance(visual_diagnosis, dict):
            raise ValueError("Provider returned a non-object image diagnosis.")
        crop_hint = str(visual_diagnosis.get("suspected_crop", ""))
        grounded_context = get_relevant_knowledge(
            f"{question} {crop_hint}", language=resolved_language
        )
        advisory = normalize_advisory(
            provider.generate_advisory(
                visual_diagnosis, question, grounded_context, language=resolved_language
            ),
            language=resolved_language,
        )
    except Exception as error:
        logger.exception("Diagnosis generation failed for session %s", session_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message_urdu": _local("ur", "service_unavailable"),
                "message_english": _local("en", "service_unavailable"),
                "language": resolved_language,
            },
        ) from error

    reference_images: list[dict] = []
    try:
        seen_reference_urls: set[str] = set()
        for record in get_relevant_records(f"{question} {crop_hint}"):
            for reference in resolve_reference_images(record):
                if reference["url"] not in seen_reference_urls:
                    seen_reference_urls.add(reference["url"])
                    reference_images.append(reference)
    except Exception:
        logger.exception("Reference image lookup failed for session %s", session_id)

    audio_url: str | None = None
    tts_notice: str | None = None
    try:
        spoken_text = (
            advisory.get("spoken_explanation_english")
            if resolved_language == "en"
            else advisory.get("spoken_explanation_urdu")
        ) or advisory.get("spoken_explanation_urdu")
        generated_audio = provider.text_to_speech(
            spoken_text, language=resolved_language
        )
        if generated_audio:
            output_path = settings.audio_dir / f"{session_id}.wav"
            output_path.write_bytes(generated_audio)
            audio_url = _media_url(output_path)
    except Exception:
        logger.exception("Speech generation failed for session %s", session_id)
        tts_notice = _local(resolved_language, "tts_failed")

    save_session(
        session_id=session_id,
        image_path=image_path,
        audio_input_path=audio_path,
        question=question,
        transcript=transcript,
        advisory=advisory,
        audio_url=audio_url,
        provider=provider.provider_name,
        is_demo=provider.is_demo,
        language=resolved_language,
    )

    visual_symptoms = (
        visual_diagnosis.get("visual_symptoms_english")
        if resolved_language == "en"
        else visual_diagnosis.get("visual_symptoms_urdu")
    ) or visual_diagnosis.get("visual_symptoms_urdu", "")

    return {
        "session_id": session_id,
        "provider": provider.provider_name,
        "is_demo": provider.is_demo,
        "language": resolved_language,
        "image_url": _media_url(image_path),
        "reference_images": reference_images,
        "question": question,
        "transcript": transcript,
        "audio_notice": audio_notice,
        "tts_notice": tts_notice,
        "visual_symptoms": visual_symptoms,
        "visual_symptoms_urdu": visual_diagnosis.get("visual_symptoms_urdu", ""),
        "visual_symptoms_english": visual_diagnosis.get("visual_symptoms_english", ""),
        "audio_url": audio_url,
        **advisory,
    }
