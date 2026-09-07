"""FastAPI application entry point for FasalDoc."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.ai import get_provider
from backend.config import settings
from backend.database import init_db
from backend.routes.diagnose import router as diagnose_router
from backend.routes.history import router as history_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        settings.audio_dir.mkdir(parents=True, exist_ok=True)
        init_db()
    except Exception:
        logger.warning("Skipping local disk writes (read-only filesystem detected).")
    provider = get_provider()
    if provider.is_demo:
        logger.warning("No Gemini API key configured: FasalDoc is running in visibly labelled demo mode.")
    else:
        logger.info("FasalDoc is using the %s provider.", provider.provider_name)
    yield


app = FastAPI(
    title="FasalDoc API",
    description="Voice-and-photo crop guidance for Pakistani farmers.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnose_router)
app.include_router(history_router)
if settings.frontend_dir.is_dir():
    app.mount("/static", StaticFiles(directory=settings.frontend_dir), name="static")
if settings.storage_dir.is_dir():
    app.mount("/media", StaticFiles(directory=settings.storage_dir), name="media")


@app.get("/api/health")
def health() -> dict:
    provider = get_provider()
    return {
        "status": "ok",
        "provider": provider.provider_name,
        "is_demo": provider.is_demo,
        "gemini_key_configured": bool(settings.gemini_api_key),
    }


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    return FileResponse(settings.frontend_dir / "index.html")
