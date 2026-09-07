"""Small SQLite persistence layer for diagnosis history."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import DEFAULT_LANGUAGE, settings


def _connect() -> sqlite3.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_language_column(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
    }
    if "language" in columns:
        return
    try:
        connection.execute(
            f"ALTER TABLE sessions ADD COLUMN language TEXT DEFAULT '{DEFAULT_LANGUAGE}'"
        )
    except sqlite3.OperationalError:
        pass


def init_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                image_path TEXT NOT NULL,
                audio_input_path TEXT,
                question TEXT,
                transcript TEXT,
                advisory_json TEXT NOT NULL,
                confidence_score INTEGER NOT NULL,
                is_uncertain INTEGER NOT NULL,
                audio_url TEXT,
                provider TEXT NOT NULL,
                is_demo INTEGER NOT NULL DEFAULT 0,
                language TEXT NOT NULL DEFAULT 'ur'
            )
            """
        )
        _ensure_language_column(connection)


def save_session(
    *,
    session_id: str,
    image_path: Path,
    audio_input_path: Path | None,
    question: str,
    transcript: str | None,
    advisory: dict[str, Any],
    audio_url: str | None,
    provider: str,
    is_demo: bool,
    language: str = DEFAULT_LANGUAGE,
) -> None:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO sessions (
                id, created_at, image_path, audio_input_path, question, transcript,
                advisory_json, confidence_score, is_uncertain, audio_url, provider, is_demo,
                language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                created_at,
                str(image_path),
                str(audio_input_path) if audio_input_path else None,
                question,
                transcript,
                json.dumps(advisory, ensure_ascii=False),
                advisory["confidence_score"],
                int(advisory["is_uncertain"]),
                audio_url,
                provider,
                int(is_demo),
                language or DEFAULT_LANGUAGE,
            ),
        )


def list_sessions(limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as connection:
        _ensure_language_column(connection)
        rows = connection.execute(
            """
            SELECT id, created_at, question, transcript, advisory_json, confidence_score,
                   is_uncertain, audio_url, provider, is_demo, language
            FROM sessions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "question": row["question"],
            "transcript": row["transcript"],
            "advisory": json.loads(row["advisory_json"]),
            "confidence_score": row["confidence_score"],
            "is_uncertain": bool(row["is_uncertain"]),
            "audio_url": row["audio_url"],
            "provider": row["provider"],
            "is_demo": bool(row["is_demo"]),
            "language": row["language"] or DEFAULT_LANGUAGE,
        }
        for row in rows
    ]
