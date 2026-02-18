"""
LinkedIn Post Exporter — FastAPI Backend

Entry point for the application. This backend:
  - Accepts scraped LinkedIn data from the Chrome extension
  - Stores data in CSV and/or PostgreSQL (configurable via app/config.py)
  - Tracks email delivery statuses
  - Does NOT auto-trigger emails (unlike ./send-email/)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import STORE_IN_DB, STORE_IN_CSV
from app.database.connection import init_db
from app.routes.posts import router as posts_router


# ========================
#  Lifespan — startup / shutdown
# ========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on app startup and shutdown."""
    # --- Startup ---
    print("=" * 60)
    print("  LinkedIn Post Exporter — Backend Starting")
    print("=" * 60)
    print(f"  Storage → CSV: {'✓ Enabled' if STORE_IN_CSV else '✗ Disabled'}")
    print(f"  Storage → DB:  {'✓ Enabled' if STORE_IN_DB else '✗ Disabled'}")

    if not STORE_IN_CSV and not STORE_IN_DB:
        print("  ⚠ WARNING: No storage backend is enabled!")
        print("  Edit app/config.py to enable STORE_IN_CSV and/or STORE_IN_DB")

    if STORE_IN_DB:
        init_db()

    print("=" * 60)
    print("  Server is ready. Endpoints:")
    print("    POST /posts          — Receive scraped LinkedIn posts")
    print("    POST /email-status   — Record email delivery status")
    print("    GET  /health         — Health check")
    print("=" * 60)

    yield

    # --- Shutdown ---
    print("\n[Server] Shutting down gracefully...")


# ========================
#  App Instance
# ========================

app = FastAPI(
    title="LinkedIn Post Exporter API",
    description="Backend for storing scraped LinkedIn data and tracking email statuses.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Chrome extension and local dev tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # Chrome extension runs from any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(posts_router)
