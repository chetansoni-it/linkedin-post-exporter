# `routes/` — API Endpoints

This module defines all the HTTP endpoints exposed by the FastAPI backend.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package initializer |
| `posts.py` | All API route definitions |

## Endpoints

### `POST /posts` — Receive Scraped Posts

Accepts a batch of scraped LinkedIn posts from the Chrome extension.

**Request Body** (`PostBatchRequest`):
```json
{
  "batch_number": 1,
  "posts": [
    {
      "author": "John Doe",
      "timestamp": "2h",
      "emails": "john@company.com, hr@company.com",
      "contact_numbers": "+1234567890",
      "apply_links": "https://apply.example.com",
      "content": "We are hiring a DevOps Engineer..."
    }
  ]
}
```

**Response** (`PostBatchResponse`):
```json
{
  "status": "ok",
  "message": "Batch 1 processed successfully.",
  "batch_number": 1,
  "total_received": 1,
  "new_posts": 1,
  "duplicates_skipped": 0
}
```

---

### `POST /send-emails` — Send Emails to Provided List

Sends emails to a list of recipients with the configured template and resume attachment. Designed for future WebUI integration.

**Request Body** (`SendEmailRequest`):
```json
{
  "emails": ["hr@company.com", "recruiter@startup.io"],
  "skip_duplicates": true,
  "author": "John Doe",
  "content": "LinkedIn post content..."
}
```

**Response** (`SendEmailResponse`):
```json
{
  "status": "ok",
  "message": "Successfully sent 2 email(s).",
  "sent": 2,
  "failed": 0,
  "failed_details": [],
  "duplicates_skipped": 0,
  "company_matches_skipped": 0
}
```

---

### `POST /trigger-emails` — Start Background Email Job ★

Triggers a background job that:
1. Reads all stored posts from CSV/DB
2. Extracts email addresses from posts
3. Deduplicates against the sent-mails log
4. Sends emails one-by-one via SMTP

Returns immediately — use `GET /email-job-status` to monitor progress.

**Response** (`TriggerEmailResponse`):
```json
{
  "status": "ok",
  "message": "Email job started in background. Check GET /email-job-status for progress."
}
```

---

### `GET /email-job-status` — Check Email Job Progress

Returns the current (or last) background email job status with real-time progress.

**Response** (`EmailJobStatusResponse`):
```json
{
  "status": "running",
  "phase": "sending",
  "started_at": "2025-02-18T10:30:00+00:00",
  "total_emails_found": 50,
  "total_to_send": 35,
  "duplicates_skipped": 15,
  "sent": 12,
  "failed": 0,
  "current": 13,
  "current_email": "recruiter@company.com"
}
```

---

### `GET /health` — Health Check

Returns the current server status and storage configuration.

**Response** (`HealthResponse`):
```json
{
  "status": "healthy",
  "storage_csv": true,
  "storage_db": false,
  "timestamp": "2025-02-18T10:30:00+00:00"
}
```

## How to Use

All routes are registered automatically when the app starts. Test them using:

- **Swagger UI**: `http://localhost:8000/docs`
- **cURL**:
  ```bash
  # Health check
  curl http://localhost:8000/health

  # Trigger background email job
  curl -X POST http://localhost:8000/trigger-emails

  # Check email job status
  curl http://localhost:8000/email-job-status
  ```

## Adding New Routes

1. Define the endpoint in `posts.py` (or create a new route file)
2. Create request/response schemas in `app/models/schemas.py`
3. If using a new file, register it in `app/main.py`:
   ```python
   from app.routes.new_routes import router as new_router
   app.include_router(new_router)
   ```
