"""
PostgreSQL storage backend using SQLAlchemy.

Handles reading, writing, and deduplication for LinkedIn posts
stored in the database.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.connection import LinkedInPost


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


def get_all_posts(db: Session) -> list[dict]:
    """Reads all posts from the database and returns them as a list of dicts."""
    stmt = select(LinkedInPost).order_by(LinkedInPost.id)
    results = db.execute(stmt).scalars().all()

    posts = []
    for row in results:
        posts.append({
            "author": row.author,
            "timestamp": row.timestamp,
            "emails": row.emails,
            "contact_numbers": row.contact_numbers,
            "apply_links": row.apply_links,
            "content": row.content,
            "content_hash": row.content_hash,
            "batch_number": row.batch_number,
            "created_at": str(row.created_at) if row.created_at else "",
        })

    return posts
