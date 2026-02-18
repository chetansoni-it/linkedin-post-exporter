"""
Database connection and table setup.

Uses the PostgreSQL instance defined in ./db/docker-compose.yaml:
  - Host: localhost:5432
  - Credentials: root/root
  - Database: test_db
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from datetime import datetime, timezone

from app.config import DATABASE_URL, STORE_IN_DB


# ========================
#  SQLAlchemy Base & Engine
# ========================

class Base(DeclarativeBase):
    pass


# Only create engine if DB storage is enabled
engine = None
SessionLocal = None

if STORE_IN_DB:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ========================
#  Table Definitions
# ========================

class LinkedInPost(Base):
    """Stores scraped LinkedIn post data received from the Chrome extension."""
    __tablename__ = "linkedin_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(255), nullable=False, default="Unknown")
    timestamp = Column(String(50), nullable=False, default="Unknown")
    emails = Column(Text, nullable=False, default="")
    contact_numbers = Column(Text, nullable=False, default="")
    apply_links = Column(Text, nullable=False, default="")
    content = Column(Text, nullable=False, default="")
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    batch_number = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_linkedin_posts_author", "author"),
    )


class EmailStatus(Base):
    """Tracks email delivery statuses linked to scraped data."""
    __tablename__ = "email_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_email = Column(String(320), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    author = Column(String(255), nullable=False, default="")
    error_message = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("recipient_email", name="uq_email_status_recipient"),
    )


# ========================
#  Init Helper
# ========================

def init_db():
    """Creates all tables if they don't already exist. Called at app startup."""
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        print("[DB] Tables created / verified successfully.")
    else:
        print("[DB] Database storage is disabled — skipping table creation.")


def get_db():
    """FastAPI dependency — yields a DB session and ensures cleanup."""
    if SessionLocal is None:
        raise RuntimeError("Database storage is disabled. Enable STORE_IN_DB in config.py")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
