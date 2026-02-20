# `services/` — Business Logic Layer

This module contains the core business logic for storage orchestration, email sending, and background job management. Routes in `app/routes/` delegate all heavy lifting to these services.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package initializer |
| `storage.py` | Storage orchestration — routes data to CSV/DB with smart deduplication |
| `email.py` | Core SMTP email sending — template reading, attachments, duplicate checking |
| `email_job.py` | Background email job runner — triggered via API, runs in a separate thread |

---

## `storage.py` — Storage Orchestration

Central logic that reads config toggles and routes post data to the correct backend(s).

### Deduplication Priority

| Scenario | Dedup Source |
|---|---|
| `STORE_IN_DB = True` | PostgreSQL (authoritative, even if CSV is also enabled) |
| `STORE_IN_CSV = True` (DB off) | CSV file |
| Both disabled | Returns error |

### Key Functions

| Function | Description |
|---|---|
| `process_post_batch(posts, batch_number, db)` | Deduplicates and saves a batch of posts to all enabled backends |
| `validate_storage_enabled()` | Returns an error string if no storage is enabled, else `None` |
| `get_storage_status()` | Returns a dict with current storage config for health checks |

### How It Works

1. Generates a SHA-256 `content_hash` from `author + content[:200]`
2. Checks the priority storage for existing hash
3. Builds a row dict for new posts
4. Saves to all enabled backends (DB and/or CSV)
5. Returns summary with counts

---

## `email.py` — Email Sending Service

Handles the complete email sending workflow via Gmail SMTP.

### Features

- Reads email **subject** (line 1) and **body** from `template/email_body.txt`
- Attaches all files from `resume/` directory (PDF, DOCX, etc.)
- Appends **portfolio link** and **LinkedIn post reference** to the email body
- Detects **duplicate recipients** from `sent-mails/sent-mails.csv`
- Detects **company-domain matches** (e.g., already emailed someone at `@company.com`)
- Skips common public email domains (Gmail, Yahoo, Hotmail, etc.) for company matching
- Logs every successful send to `sent-mails/sent-mails.csv`

### Key Functions

| Function | Description |
|---|---|
| `send_email_to_recipients(emails, metadata, skip_duplicates)` | Main entry point — validates, deduplicates, sends, and returns summary |
| `validate_email_config()` | Checks if `SENDER_EMAIL` and `SENDER_PASSWORD` are set |
| `check_duplicates(emails)` | Returns clean/duplicate/company-match lists |
| `read_template()` | Reads subject and body from the template file |
| `get_attachments()` | Lists all files in the `resume/` directory |
| `create_message(recipient, subject, body, attachments, metadata)` | Builds the full MIME email message |
| `log_sent_email(recipient, metadata)` | Appends a record to the sent-mails CSV |

---

## `email_job.py` — Background Email Job

Runs as a **background thread** so the API responds immediately while emails are sent in parallel.

### Job Flow

```
POST /trigger-emails
    ↓
1. Read all posts from CSV or DB
2. Extract unique email addresses from posts
3. Deduplicate against sent-mails log
4. Send emails one-by-one via SMTP
5. Update job status in real-time
    ↓
GET /email-job-status  (poll for progress)
```

### Job Phases

| Phase | Description |
|---|---|
| `starting` | Job initialized |
| `reading_posts` | Loading posts from storage |
| `extracting_emails` | Parsing email addresses from post content |
| `deduplicating` | Checking against sent-mails log |
| `sending` | Actively sending emails |
| `done` | Job completed (or failed) |

### Key Functions

| Function | Description |
|---|---|
| `trigger_email_job()` | Pre-flight checks, initializes job status, launches background thread |
| `get_job_status()` | Returns current/last job status (thread-safe) |
| `is_job_running()` | Returns `True` if a job is currently in progress |

### Thread Safety

- Job status is stored in a module-level `_current_job` dict
- All reads/writes are protected by `_job_lock` (a `threading.Lock`)
- Only one job can run at a time — concurrent trigger requests are rejected

## How to Use

These services are called by the route handlers. You typically don't call them directly, but you can:

```python
from app.services.storage import process_post_batch
from app.services.email import send_email_to_recipients
from app.services.email_job import trigger_email_job, get_job_status
```
