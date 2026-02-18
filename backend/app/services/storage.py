"""
Storage orchestration service.

Central logic that:
1. Reads the config toggles (STORE_IN_CSV, STORE_IN_DB)
2. Routes data to the correct backend(s)
3. Implements smart validation/deduplication priority:
   - If STORE_IN_DB is True  → validate against PostgreSQL (even if CSV is also on)
   - If only STORE_IN_CSV    → validate against CSV
   - If both are disabled    → return error
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import STORE_IN_CSV, STORE_IN_DB
from app.storage import csv_storage, db_storage
from app.storage.csv_storage import generate_content_hash
from app.models.schemas import LinkedInPostData, EmailStatusUpdate


# ========================
#  Storage Status
# ========================

def get_storage_status() -> dict:
    """Returns the current storage configuration for health checks."""
    return {
        "csv_enabled": STORE_IN_CSV,
        "db_enabled": STORE_IN_DB,
        "active": STORE_IN_CSV or STORE_IN_DB,
    }


def validate_storage_enabled() -> str | None:
    """Returns an error message if no storage backend is enabled, else None."""
    if not STORE_IN_CSV and not STORE_IN_DB:
        return (
            "No storage backend is enabled. "
            "Set STORE_IN_CSV=True and/or STORE_IN_DB=True in app/config.py"
        )
    return None


# ========================
#  Post Processing
# ========================

def process_post_batch(
    posts: list[LinkedInPostData],
    batch_number: int,
    db: Session | None = None,
) -> dict:
    """
    Processes a batch of LinkedIn posts with deduplication and dual storage.

    Validation priority:
      1. If STORE_IN_DB is True → check DB for duplicates (authoritative source)
      2. Else if STORE_IN_CSV   → check CSV for duplicates
      3. Else                   → error (caught earlier by validate_storage_enabled)

    Returns a summary dict with counts.
    """
    now = datetime.now(timezone.utc)
    new_posts: list[dict] = []
    duplicates_skipped = 0

    # --- Pre-load CSV hashes if CSV-only validation ---
    csv_hashes: set[str] | None = None
    if not STORE_IN_DB and STORE_IN_CSV:
        csv_hashes = csv_storage.get_existing_post_hashes()

    for post in posts:
        content_hash = generate_content_hash(post.author, post.content)

        # --- Deduplication check (priority: DB > CSV) ---
        is_duplicate = False

        if STORE_IN_DB and db is not None:
            is_duplicate = db_storage.is_post_duplicate(db, content_hash)
        elif STORE_IN_CSV and csv_hashes is not None:
            is_duplicate = content_hash in csv_hashes

        if is_duplicate:
            duplicates_skipped += 1
            continue

        # Build the row dict used by both backends
        post_dict = {
            "author": post.author,
            "timestamp": post.timestamp,
            "emails": post.emails,
            "contact_numbers": post.contact_numbers,
            "apply_links": post.apply_links,
            "content": post.content,
            "content_hash": content_hash,
            "batch_number": batch_number,
            "created_at": now,
        }
        new_posts.append(post_dict)

        # Track hash in the local set so the same batch doesn't insert duplicates
        if csv_hashes is not None:
            csv_hashes.add(content_hash)

    # --- Persist to enabled backends ---
    db_count = 0
    csv_count = 0

    if new_posts:
        if STORE_IN_DB and db is not None:
            db_count = db_storage.save_posts(db, new_posts)

        if STORE_IN_CSV:
            # Convert datetime to ISO string for CSV
            csv_rows = []
            for p in new_posts:
                row = dict(p)
                row["created_at"] = row["created_at"].isoformat()
                csv_rows.append(row)
            csv_count = csv_storage.save_posts(csv_rows)

    return {
        "total_received": len(posts),
        "new_posts": len(new_posts),
        "duplicates_skipped": duplicates_skipped,
        "saved_to_db": db_count,
        "saved_to_csv": csv_count,
    }


# ========================
#  Email Status Processing
# ========================

def process_email_status(
    update: EmailStatusUpdate,
    db: Session | None = None,
) -> dict:
    """
    Processes an email delivery status update with dual storage.

    Returns a summary dict.
    """
    now = datetime.now(timezone.utc)

    status_dict = {
        "recipient_email": update.recipient_email.strip().lower(),
        "status": update.status,
        "author": update.author,
        "error_message": update.error_message,
        "updated_at": now,
    }

    if STORE_IN_DB and db is not None:
        db_storage.save_email_status(db, status_dict)

    if STORE_IN_CSV:
        csv_row = dict(status_dict)
        csv_row["updated_at"] = csv_row["updated_at"].isoformat()
        csv_storage.save_email_status(csv_row)

    return {
        "recipient_email": status_dict["recipient_email"],
        "status": status_dict["status"],
        "stored_in_db": STORE_IN_DB,
        "stored_in_csv": STORE_IN_CSV,
    }
