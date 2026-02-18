"""
Pydantic schemas for request/response validation.

These models mirror the data structure sent by the Chrome extension
(see chrome-extension/content.js → extractSinglePost function).
"""

from pydantic import BaseModel, Field
from typing import Optional


# ========================
#  Chrome Extension Data
# ========================

class LinkedInPostData(BaseModel):
    """Single LinkedIn post payload — matches the JSON shape from the Chrome extension."""
    author: str = Field(default="Unknown", description="Post author name")
    timestamp: str = Field(default="Unknown", description="Relative timestamp (e.g., '2h', '3d')")
    emails: str = Field(default="", description="Comma-separated emails extracted from post content")
    contact_numbers: str = Field(default="", description="Comma-separated phone numbers from post")
    apply_links: str = Field(default="", description="Comma-separated application URLs from post")
    content: str = Field(default="", description="Full text content of the LinkedIn post")


class PostBatchRequest(BaseModel):
    """Batch payload sent by the Chrome extension (see config.js → BATCH_SIZE)."""
    batch_number: int = Field(ge=1, description="Sequential batch number in the current session")
    posts: list[LinkedInPostData] = Field(description="List of scraped LinkedIn posts")




# ========================
#  API Responses
# ========================

class PostBatchResponse(BaseModel):
    """Response returned after processing a batch of posts."""
    status: str
    message: str
    batch_number: int
    total_received: int
    new_posts: int
    duplicates_skipped: int




class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    storage_csv: bool
    storage_db: bool
    timestamp: str


# ========================
#  Email Sending
# ========================

class SendEmailRequest(BaseModel):
    """Request to send emails to a list of recipients."""
    emails: list[str] = Field(description="List of recipient email addresses")
    skip_duplicates: bool = Field(default=True, description="Skip already-contacted emails")
    author: str = Field(default="", description="LinkedIn post author for reference in email body")
    content: str = Field(default="", description="LinkedIn post content for reference")
    contact_numbers: str = Field(default="", description="Contact numbers from LinkedIn post")
    apply_links: str = Field(default="", description="Apply links from LinkedIn post")


class SendEmailResponse(BaseModel):
    """Response after attempting to send emails."""
    status: str
    message: str
    sent: int
    failed: int
    failed_details: list[dict] = Field(default_factory=list)
    duplicates_skipped: int = Field(default=0)
    company_matches_skipped: int = Field(default=0)


# ========================
#  Email Job (trigger-based)
# ========================

class TriggerEmailResponse(BaseModel):
    """Response from POST /trigger-emails."""
    status: str
    message: str


class EmailJobStatusResponse(BaseModel):
    """Response from GET /email-job-status."""
    status: str
    phase: str = Field(default="", description="Current phase: starting, reading_posts, extracting_emails, deduplicating, sending, done")
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    message: str = ""
    total_emails_found: int = 0
    total_to_send: int = 0
    duplicates_skipped: int = 0
    company_matches_skipped: int = 0
    sent: int = 0
    failed: int = 0
    failed_details: list[dict] = Field(default_factory=list)
    current: int = Field(default=0, description="Current email index being sent")
    current_email: str = Field(default="", description="Email address currently being sent to")

