"""
API routes for LinkedIn post data and email status tracking.

Endpoints:
  POST /posts           — Receive a batch of scraped LinkedIn posts
  POST /email-status    — Record an email delivery status update
  GET  /health          — Health check with storage configuration info
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.config import STORE_IN_CSV, STORE_IN_DB
from app.database.connection import get_db
from app.models.schemas import (
    PostBatchRequest,
    PostBatchResponse,
    EmailStatusUpdate,
    EmailStatusResponse,
    HealthResponse,
)
from app.services.storage import (
    process_post_batch,
    process_email_status,
    validate_storage_enabled,
)


router = APIRouter()


# ========================
#  Dependency — optional DB session
# ========================

def get_optional_db():
    """Yields a DB session if STORE_IN_DB is enabled, else yields None."""
    if STORE_IN_DB:
        yield from get_db()
    else:
        yield None


# ========================
#  POST /posts
# ========================

@router.post("/posts", response_model=PostBatchResponse)
async def receive_posts(
    payload: PostBatchRequest,
    db: Session | None = Depends(get_optional_db),
):
    """
    Receives a batch of scraped LinkedIn posts from the Chrome extension.

    - Validates that at least one storage backend is enabled
    - Deduplicates against the priority store (DB > CSV)
    - Saves new posts to all enabled backends
    - Does NOT trigger any email sending (unlike the send-email project)
    """
    # Check that storage is configured
    error = validate_storage_enabled()
    if error:
        raise HTTPException(status_code=503, detail=error)

    if not payload.posts:
        return PostBatchResponse(
            status="ok",
            message="Empty batch received — nothing to process.",
            batch_number=payload.batch_number,
            total_received=0,
            new_posts=0,
            duplicates_skipped=0,
        )

    result = process_post_batch(
        posts=payload.posts,
        batch_number=payload.batch_number,
        db=db,
    )

    return PostBatchResponse(
        status="ok",
        message=f"Batch {payload.batch_number} processed successfully.",
        batch_number=payload.batch_number,
        total_received=result["total_received"],
        new_posts=result["new_posts"],
        duplicates_skipped=result["duplicates_skipped"],
    )


# ========================
#  POST /email-status
# ========================

@router.post("/email-status", response_model=EmailStatusResponse)
async def update_email_status(
    update: EmailStatusUpdate,
    db: Session | None = Depends(get_optional_db),
):
    """
    Records an email delivery status update.

    Accepts statuses like 'sent', 'failed', 'bounced', 'delivered'
    and stores them in the enabled backends.
    """
    error = validate_storage_enabled()
    if error:
        raise HTTPException(status_code=503, detail=error)

    result = process_email_status(update=update, db=db)

    return EmailStatusResponse(
        status="ok",
        message=f"Email status for '{result['recipient_email']}' recorded as '{result['status']}'.",
        recipient_email=result["recipient_email"],
    )


# ========================
#  GET /health
# ========================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns the current storage configuration and server status."""
    return HealthResponse(
        status="healthy",
        storage_csv=STORE_IN_CSV,
        storage_db=STORE_IN_DB,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
