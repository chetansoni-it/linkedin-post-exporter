"""
API routes for LinkedIn post data, email status tracking, and email sending.

Endpoints:
  POST /posts              — Receive a batch of scraped LinkedIn posts

  POST /send-emails        — Send emails to a provided list (for future WebUI)
  POST /trigger-emails     — Start background email job from stored data
  GET  /email-job-status   — Check progress of background email job
  GET  /health             — Health check with storage configuration info
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.config import STORE_IN_CSV, STORE_IN_DB
from app.database.connection import get_db
from app.models.schemas import (
    PostBatchRequest,
    PostBatchResponse,
    HealthResponse,
    SendEmailRequest,
    SendEmailResponse,
    TriggerEmailResponse,
    EmailJobStatusResponse,
)
from app.services.email import send_email_to_recipients, validate_email_config
from app.services.email_job import trigger_email_job, get_job_status
from app.services.storage import (
    process_post_batch,
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
#  POST /send-emails
# ========================

@router.post("/send-emails", response_model=SendEmailResponse)
async def send_emails(payload: SendEmailRequest):
    """
    Sends emails to the provided list of recipients.

    - Uses template from template/email_body.txt (Subject on line 1, body below)
    - Attaches all files from resume/ directory (PDF, DOCX, etc.)
    - Checks sent-mails/sent-mails.csv for duplicates & company-domain matches
    - Logs successful sends to sent-mails/sent-mails.csv
    - Credentials loaded from .env (SENDER_EMAIL, SENDER_PASSWORD)
    """
    # Validate email config
    config_error = validate_email_config()
    if config_error:
        raise HTTPException(status_code=503, detail=config_error)

    if not payload.emails:
        return SendEmailResponse(
            status="ok",
            message="No emails provided.",
            sent=0,
            failed=0,
        )

    # Build metadata from request
    metadata = {
        "author": payload.author,
        "content": payload.content,
        "contact_numbers": payload.contact_numbers,
        "apply_links": payload.apply_links,
    }

    result = send_email_to_recipients(
        emails=payload.emails,
        metadata=metadata,
        skip_duplicates=payload.skip_duplicates,
    )

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    return SendEmailResponse(
        status="ok",
        message=result.get("message", "Emails processed."),
        sent=result["sent"],
        failed=result["failed"],
        failed_details=result.get("failed_details", []),
        duplicates_skipped=result.get("duplicates_skipped", 0),
        company_matches_skipped=result.get("company_matches_skipped", 0),
    )


# ========================
#  POST /trigger-emails
# ========================

@router.post("/trigger-emails", response_model=TriggerEmailResponse)
async def trigger_emails():
    """
    Starts the background email sending job.

    Reads all stored posts from CSV/DB, extracts emails,
    deduplicates against sent-mails log, and sends emails in background.
    Returns immediately — check GET /email-job-status for progress.
    """
    result = trigger_email_job()

    if result.get("error"):
        raise HTTPException(status_code=503, detail=result["error"])

    return TriggerEmailResponse(
        status="ok",
        message=result["message"],
    )


# ========================
#  GET /email-job-status
# ========================

@router.get("/email-job-status", response_model=EmailJobStatusResponse)
async def email_job_status():
    """
    Returns the current (or last) background email job status.

    Includes: phase, progress, sent/failed counts, current email being sent.
    """
    job = get_job_status()

    if job is None:
        return EmailJobStatusResponse(
            status="idle",
            message="No email job has been triggered yet. Use POST /trigger-emails to start.",
        )

    return EmailJobStatusResponse(**job)


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
