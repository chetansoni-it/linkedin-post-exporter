"""
Entry point for `fastapi dev main.py` or `uvicorn main:app`.

Re-exports the FastAPI app instance from the app package.
"""

from app.main import app  # noqa: F401
