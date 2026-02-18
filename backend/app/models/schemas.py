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
#  Email Status Tracking
# ========================

class EmailStatusUpdate(BaseModel):
    """Payload for tracking email delivery status updates."""
    recipient_email: str = Field(description="The email address the message was sent to")
    status: str = Field(description="Delivery status: 'sent', 'failed', 'bounced', 'delivered'")
    author: str = Field(default="", description="LinkedIn post author for reference")
    error_message: Optional[str] = Field(default=None, description="Error details if status is 'failed'")


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


class EmailStatusResponse(BaseModel):
    """Response returned after processing an email status update."""
    status: str
    message: str
    recipient_email: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    storage_csv: bool
    storage_db: bool
    timestamp: str
