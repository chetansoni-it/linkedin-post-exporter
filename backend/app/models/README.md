# `models/` — Pydantic Schemas

This module defines all Pydantic models used for **request validation** and **response serialization** across the API.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package initializer |
| `schemas.py` | All Pydantic models for the API |

## Schema Overview

### Request Models

| Model | Used By | Description |
|---|---|---|
| `LinkedInPostData` | `POST /posts` | Single LinkedIn post payload — matches the JSON shape sent by the Chrome extension |
| `PostBatchRequest` | `POST /posts` | Wrapper with `batch_number` and a list of `LinkedInPostData` |
| `SendEmailRequest` | `POST /send-emails` | List of recipient emails + optional metadata (author, content, etc.) |

### Response Models

| Model | Used By | Description |
|---|---|---|
| `PostBatchResponse` | `POST /posts` | Summary of batch processing (new posts, duplicates skipped) |
| `HealthResponse` | `GET /health` | Server status and storage config |
| `SendEmailResponse` | `POST /send-emails` | Email sending result (sent, failed, skipped counts) |
| `TriggerEmailResponse` | `POST /trigger-emails` | Acknowledgement that the background job started |
| `EmailJobStatusResponse` | `GET /email-job-status` | Detailed progress of the background email job |

## Field Highlights

### `LinkedInPostData`

```python
author: str          # Post author name (default: "Unknown")
timestamp: str       # Relative timestamp, e.g., "2h", "3d"
emails: str          # Comma-separated emails from post content
contact_numbers: str # Comma-separated phone numbers
apply_links: str     # Comma-separated application URLs
content: str         # Full text content of the LinkedIn post
```

### `EmailJobStatusResponse`

Provides real-time tracking of the background email job:

```python
status: str              # "running", "completed", or "failed"
phase: str               # "starting", "reading_posts", "extracting_emails",
                         # "deduplicating", "sending", "done"
started_at: str          # ISO timestamp when job started
finished_at: str | None  # ISO timestamp when job finished
total_emails_found: int  # Total emails extracted from posts
total_to_send: int       # Emails remaining after dedup
duplicates_skipped: int  # Emails already sent before
sent: int                # Successfully sent count
failed: int              # Failed send count
current: int             # Index of current email being sent
current_email: str       # Email address currently being processed
```

## How to Use

Import schemas in your routes or services:

```python
from app.models.schemas import PostBatchRequest, PostBatchResponse

@router.post("/posts", response_model=PostBatchResponse)
async def receive_posts(payload: PostBatchRequest):
    ...
```

## Adding New Schemas

1. Define the Pydantic model in `schemas.py`
2. Use `Field(...)` for descriptions and validation
3. Import it in the route that needs it
