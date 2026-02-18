"""
Top-level entry point for: uv run fastapi dev main.py

Re-exports the FastAPI app instance from the app package.
"""

from app.main import app  # noqa: F401
