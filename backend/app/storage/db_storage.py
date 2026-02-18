"""
PostgreSQL storage backend using SQLAlchemy.

Handles reading, writing, and deduplication for LinkedIn posts
and email statuses stored in the database.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.connection import LinkedInPost, EmailStatus


# ========================
#  Posts — Read / Write / Check
# ========================

def is_post_duplicate(db: Session, content_hash: str) -> bool:
    """Checks if a post with this content_hash already exists in the DB."""
    stmt = select(LinkedInPost.id).where(LinkedInPost.content_hash == content_hash).limit(1)
    result = db.execute(stmt).first()
    return result is not None


def save_posts(db: Session, posts: list[dict]) -> int:
    """Inserts a list of post dicts into the database. Returns number of rows inserted."""
    count = 0
    for post_data in posts:
        post = LinkedInPost(
            author=post_data["author"],
            timestamp=post_data["timestamp"],
            emails=post_data["emails"],
            contact_numbers=post_data["contact_numbers"],
            apply_links=post_data["apply_links"],
            content=post_data["content"],
            content_hash=post_data["content_hash"],
            batch_number=post_data.get("batch_number"),
            created_at=post_data.get("created_at", datetime.now(timezone.utc)),
        )
        db.add(post)
        count += 1

    db.commit()
    return count


# ========================
#  Email Status — Read / Write / Check
# ========================

def get_email_status(db: Session, recipient_email: str) -> EmailStatus | None:
    """Retrieves the current email status record for a given recipient."""
    stmt = select(EmailStatus).where(
        EmailStatus.recipient_email == recipient_email.strip().lower()
    )
    return db.execute(stmt).scalar_one_or_none()


def save_email_status(db: Session, data: dict) -> None:
    """Inserts or updates an email status record (upsert logic)."""
    recipient = data["recipient_email"].strip().lower()
    existing = get_email_status(db, recipient)

    if existing:
        # Update existing record
        existing.status = data["status"]
        existing.author = data.get("author", existing.author)
        existing.error_message = data.get("error_message")
        existing.updated_at = datetime.now(timezone.utc)
    else:
        # Insert new record
        record = EmailStatus(
            recipient_email=recipient,
            status=data["status"],
            author=data.get("author", ""),
            error_message=data.get("error_message"),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(record)

    db.commit()
