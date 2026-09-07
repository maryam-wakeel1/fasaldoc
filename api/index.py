import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for subdir in ("storage", "storage/uploads", "storage/audio"):
    try:
        (ROOT / subdir).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

from backend.main import app  # noqa: E402, F401
