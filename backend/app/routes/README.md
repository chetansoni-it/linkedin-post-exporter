# `routes/` — API Endpoints

This module defines all the HTTP endpoints exposed by the FastAPI backend.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package initializer |
| `posts.py` | All API route definitions |

---

## API Reference

### Base URL

```
http://localhost:8000
```

Interactive Swagger docs: `http://localhost:8000/docs`

---

### 1. `POST /posts` — Receive Scraped LinkedIn Posts

Accepts a batch of scraped posts from the Chrome extension, deduplicates, and stores them.

#### Sample cURL

```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "batch_number": 1,
    "posts": [
      {
        "author": "John Doe",
        "timestamp": "2h",
        "emails": "john@company.com, hr@company.com",
        "contact_numbers": "+1234567890",
        "apply_links": "https://apply.example.com/job/123",
        "content": "We are hiring a DevOps Engineer with 3+ years of experience in AWS, Terraform, and Kubernetes. Send your resume to hr@company.com"
      },
      {
        "author": "Jane Smith",
        "timestamp": "5h",
        "emails": "careers@startup.io",
        "contact_numbers": "",
        "apply_links": "https://careers.startup.io/apply",
        "content": "Looking for a Cloud Architect to join our team. Remote friendly! Apply at careers@startup.io"
      }
    ]
  }'
```

#### Expected Response — `200 OK`

```json
{
  "status": "ok",
  "message": "Batch 1 processed successfully.",
  "batch_number": 1,
  "total_received": 2,
  "new_posts": 2,
  "duplicates_skipped": 0
}
```

#### Response When Duplicates Exist

```json
{
  "status": "ok",
  "message": "Batch 2 processed successfully.",
  "batch_number": 2,
  "total_received": 2,
  "new_posts": 0,
  "duplicates_skipped": 2
}
```

#### Error Response — `503 Service Unavailable` (No storage enabled)

```json
{
  "detail": "No storage backend is enabled. Set STORE_IN_CSV=True and/or STORE_IN_DB=True in app/config.py"
}
```

---

### 2. `POST /send-emails` — Send Emails to a Provided List

Sends personalized emails with resume attachments to the given list of recipients. Checks for duplicates and company-domain matches against the sent-mails log.

#### Sample cURL

```bash
curl -X POST http://localhost:8000/send-emails \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["hr@company.com", "recruiter@startup.io", "hiring@techcorp.com"],
    "skip_duplicates": true,
    "author": "John Doe",
    "content": "We are hiring a DevOps Engineer with 3+ years of experience...",
    "contact_numbers": "+1234567890",
    "apply_links": "https://apply.example.com/job/123"
  }'
```

#### Expected Response — `200 OK`

```json
{
  "status": "ok",
  "message": "Successfully sent 3 email(s).",
  "sent": 3,
  "failed": 0,
  "failed_details": [],
  "duplicates_skipped": 0,
  "company_matches_skipped": 0
}
```

#### Response With Duplicates & Failures

```json
{
  "status": "ok",
  "message": "Successfully sent 1 email(s).",
  "sent": 1,
  "failed": 1,
  "failed_details": [
    {
      "email": "invalid@nonexistent.xyz",
      "error": "SMTPRecipientsRefused({'invalid@nonexistent.xyz': (550, 'User not found')})"
    }
  ],
  "duplicates_skipped": 2,
  "company_matches_skipped": 1
}
```

#### Error Response — `503 Service Unavailable` (Email not configured)

```json
{
  "detail": "SENDER_EMAIL is not set in .env"
}
```

---

### 3. `POST /trigger-emails` — Start Background Email Job ★

Triggers a background job that reads all stored posts, extracts emails, deduplicates, and sends emails in a separate thread. Returns **immediately** — poll `GET /email-job-status` for progress.

#### Sample cURL

```bash
curl -X POST http://localhost:8000/trigger-emails
```

#### Expected Response — `200 OK`

```json
{
  "status": "ok",
  "message": "Email job started in background. Check GET /email-job-status for progress."
}
```

#### Error Response — Job Already Running

```json
{
  "detail": "An email job is already running. Check GET /email-job-status for progress."
}
```

#### Error Response — No Storage Configured

```json
{
  "detail": "No storage backend enabled. Enable STORE_IN_CSV or STORE_IN_DB in config."
}
```

---

### 4. `GET /email-job-status` — Check Background Job Progress

Returns the current (or last completed) background email job status with real-time progress.

#### Sample cURL

```bash
curl http://localhost:8000/email-job-status
```

#### Response — Job In Progress

```json
{
  "status": "running",
  "phase": "sending",
  "started_at": "2025-02-18T10:30:00+00:00",
  "finished_at": null,
  "message": "Email job started.",
  "total_emails_found": 50,
  "total_to_send": 35,
  "duplicates_skipped": 12,
  "company_matches_skipped": 3,
  "sent": 18,
  "failed": 0,
  "failed_details": [],
  "current": 19,
  "current_email": "recruiter@techcorp.com"
}
```

#### Response — Job Completed

```json
{
  "status": "completed",
  "phase": "done",
  "started_at": "2025-02-18T10:30:00+00:00",
  "finished_at": "2025-02-18T10:35:42+00:00",
  "message": "Job complete. Sent 35 email(s), 0 failed.",
  "total_emails_found": 50,
  "total_to_send": 35,
  "duplicates_skipped": 12,
  "company_matches_skipped": 3,
  "sent": 35,
  "failed": 0,
  "failed_details": [],
  "current": 35,
  "current_email": ""
}
```

#### Response — No Job Triggered Yet

```json
{
  "status": "idle",
  "phase": "",
  "started_at": null,
  "finished_at": null,
  "message": "No email job has been triggered yet. Use POST /trigger-emails to start.",
  "total_emails_found": 0,
  "total_to_send": 0,
  "duplicates_skipped": 0,
  "company_matches_skipped": 0,
  "sent": 0,
  "failed": 0,
  "failed_details": [],
  "current": 0,
  "current_email": ""
}
```

#### Response — Job Failed

```json
{
  "status": "failed",
  "phase": "done",
  "started_at": "2025-02-18T10:30:00+00:00",
  "finished_at": "2025-02-18T10:30:05+00:00",
  "message": "SMTP connection failed: [Errno 61] Connection refused",
  "total_emails_found": 50,
  "total_to_send": 35,
  "duplicates_skipped": 12,
  "company_matches_skipped": 3,
  "sent": 0,
  "failed": 0,
  "failed_details": [],
  "current": 0,
  "current_email": ""
}
```

---

### 5. `GET /health` — Health Check

Returns the current server status and storage configuration.

#### Sample cURL

```bash
curl http://localhost:8000/health
```

#### Expected Response — `200 OK`

```json
{
  "status": "healthy",
  "storage_csv": true,
  "storage_db": false,
  "timestamp": "2025-02-18T10:30:00.123456+00:00"
}
```

---

## API Summary Table

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/posts` | Receive scraped LinkedIn posts from Chrome extension | No |
| `POST` | `/send-emails` | Send emails to a provided list of recipients | SMTP config in `.env` |
| `POST` | `/trigger-emails` | Start background email job from stored data | SMTP config in `.env` |
| `GET` | `/email-job-status` | Check progress of background email job | No |
| `GET` | `/health` | Health check with storage config info | No |

## Adding New Routes

1. Define the endpoint in `posts.py` (or create a new route file)
2. Create request/response schemas in `app/models/schemas.py`
3. If using a new file, register it in `app/main.py`:
   ```python
   from app.routes.new_routes import router as new_router
   app.include_router(new_router)
   ```
