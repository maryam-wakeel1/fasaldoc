from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"status": "FasalDoc function is running", "python": "ok"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/test-import")
def test_import():
    errors = {}
    try:
        from backend.config import settings
        errors["config"] = "ok"
    except Exception as e:
        errors["config"] = str(e)

    try:
        from backend.database import init_db
        errors["database"] = "ok"
    except Exception as e:
        errors["database"] = str(e)

    try:
        from backend.ai import get_provider
        errors["ai"] = "ok"
    except Exception as e:
        errors["ai"] = str(e)

    try:
        from backend.routes.diagnose import router
        errors["diagnose"] = "ok"
    except Exception as e:
        errors["diagnose"] = str(e)

    try:
        from backend.main import app as main_app
        errors["main"] = "ok"
    except Exception as e:
        errors["main"] = str(e)

    return errors
