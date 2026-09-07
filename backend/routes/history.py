"""Session-history endpoint."""

from fastapi import APIRouter, Query

from backend.database import list_sessions

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history")
def get_history(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return {"sessions": list_sessions(limit)}
