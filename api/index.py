import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for subdir in ("storage", "storage/uploads", "storage/audio"):
    try:
        (ROOT / subdir).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

try:
    from backend.main import app
except Exception:
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse

    app = FastAPI()
    _tb = traceback.format_exc()

    @app.get("/")
    async def debug_root() -> PlainTextResponse:
        return PlainTextResponse(
            f"FasalDoc failed to start:\n\n{_tb}",
            status_code=500,
        )

    @app.get("/api/health")
    async def debug_health() -> PlainTextResponse:
        return PlainTextResponse(
            f"FasalDoc failed to start:\n\n{_tb}",
            status_code=500,
        )

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def debug_catch_all(path: str = "") -> PlainTextResponse:
        return PlainTextResponse(
            f"FasalDoc failed to start:\n\n{_tb}",
            status_code=500,
        )
