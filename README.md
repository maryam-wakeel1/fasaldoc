# FasalDoc (فصل ڈاکٹر)

**Apni Fasal Ki Awaaz Mein Baat Karein** — a voice-and-photo-first crop guidance prototype for small and mid-scale farmers in Pakistan.

Farmers can photograph a leaf, optionally record an Urdu question, and receive a simple Urdu diagnosis, confidence score, locally grounded treatment guidance, and spoken response. A low-confidence result always asks the farmer to confirm with a nearby agricultural expert.

## What is included

- Mobile-first vanilla HTML/CSS/JavaScript interface with large camera and microphone controls.
- FastAPI multipart endpoint: `POST /api/diagnose`.
- Modular AI provider boundary under `backend/ai/`.
  - `GeminiProvider` uses Google AI Studio for vision, Urdu advisory text, audio transcription, and TTS.
  - `QwenProvider` is an explicit future Alibaba Cloud/Qwen stub.
  - `DemoProvider` keeps the application demonstrable when there is no API key. Its response is visibly labeled as sample data and must not be used as a crop diagnosis.
- JSON/Excel-backed RAG-lite local crop knowledge.
- SQLite session history in `backend/database.db`.
- UUID-named local uploads and generated WAV files in `storage/`.

## Quick start

```bash
cd fasaldoc
python -m venv .venv
# Windows Git Bash
source .venv/Scripts/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn backend.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000` in a browser.

### Google AI Studio setup

Set the following in `fasaldoc/.env`:

```env
GEMINI_API_KEY=your_google_ai_studio_key
AI_PROVIDER=auto
```

With a key, `AI_PROVIDER=auto` selects Gemini. With no key, the API selects the clearly labeled `demo` provider so the complete upload, database, audio, and UI flow can be tested. Check `GET /api/health` to see the active provider.

## API

### Diagnose a leaf

```bash
curl -X POST http://127.0.0.1:8000/api/diagnose \
  -F "image=@leaf.jpg" \
  -F "text_question=پتے پیلے کیوں ہیں؟"
```

`image` is required (`image/jpeg`, `image/png`, or `image/webp`, up to 10 MB). `audio` and `text_question` are optional. The response includes:

```json
{
  "diagnosis_urdu": "...",
  "confidence_score": 85,
  "treatment_plan_urdu": "...",
  "spoken_explanation_urdu": "...",
  "is_uncertain": false,
  "audio_url": "/media/audio/<session-id>.wav"
}
```

### Session history

```bash
curl "http://127.0.0.1:8000/api/history?limit=20"
```

## Local crop knowledge

Edit `backend/data/crop_knowledge.json` directly, or normalize an Excel workbook into that format:

```bash
python -m backend.data.data_loader path/to/crop-diseases.xlsx --output backend/data/crop_knowledge.json
```

The Excel worksheet should have a header row using fields such as `crop`, `crop_aliases`, `disease`, `symptoms`, `low_cost_remedy`, `prevention`, and `image_references`. `get_relevant_knowledge()` scores crop names, aliases, disease terms, symptoms, and farmer questions before a concise context is sent to the provider.

## Architecture

```text
frontend -> POST /api/diagnose -> route orchestration
                                  -> local crop knowledge (RAG-lite)
                                  -> AIProvider (Gemini / Demo / future Qwen)
                                  -> SQLite session history + local media files
```

Routes depend only on the `AIProvider` interface (`analyze_crop_photo`, `generate_urdu_advisory`, `speech_to_text`, `text_to_speech`). Replacing Gemini with Alibaba Model Studio later should require changes only in `backend/ai/qwen_provider.py` and the provider factory.

## Safety note

This prototype provides preliminary support only. It forces uncertainty below 65% and includes an Urdu referral to a nearby agricultural expert. Farmers should confirm potentially costly or chemical interventions with a qualified local expert.
