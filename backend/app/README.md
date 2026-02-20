# `app/` — Main Application Package

This is the core FastAPI application package. It contains all the business logic, API routes, data models, storage backends, and services that power the LinkedIn Post Exporter backend.

## Structure

```
app/
├── __init__.py          # Package initializer
├── config.py            # Centralized configuration & feature toggles
├── main.py              # FastAPI app setup, CORS, lifespan, route registration
├── database/            # PostgreSQL connection & SQLAlchemy table models
├── models/              # Pydantic schemas for request/response validation
├── routes/              # API endpoint definitions
├── services/            # Business logic (storage orchestration, email sending)
└── storage/             # Storage backend implementations (CSV, PostgreSQL)
```

## Key Files

### `config.py`

The **single source of truth** for all application settings. It controls:

| Setting | Default | Description |
|---|---|---|
| `STORE_IN_CSV` | `True` | Toggle CSV file storage |
| `STORE_IN_DB` | `False` | Toggle PostgreSQL storage |
| `CSV_DIR` | `data` | Directory for CSV files |
| `TEMPLATE_FILE` | `template/email_body.txt` | Email template path |
| `ATTACHMENT_DIR` | `resume/` | Resume attachment directory |
| `SENT_EMAILS_FILE` | `sent-mails/sent-mails.csv` | Sent email log path |

Secrets (DB credentials, SMTP passwords) are loaded from a `.env` file at the backend root — **never hardcode them here**.

### `main.py`

Creates and configures the FastAPI application:

- **Lifespan events**: Initializes the database on startup (if `STORE_IN_DB` is enabled) and prints a startup banner with storage status and available endpoints.
- **CORS middleware**: Configured with `allow_origins=["*"]` to support requests from the Chrome extension.
- **Route registration**: Includes all API routes from `app/routes/posts.py`.

## How It All Connects

```
Chrome Extension  →  POST /posts  →  routes/posts.py
                                          ↓
                                   services/storage.py  (orchestation + dedup)
                                     ↓              ↓
                              storage/csv_storage   storage/db_storage
                                     ↓              ↓
                                  data/*.csv      PostgreSQL DB

API / WebUI  →  POST /trigger-emails  →  services/email_job.py (background thread)
                                               ↓
                                         services/email.py (SMTP sending)
                                               ↓
                                         sent-mails/sent-mails.csv (logging)
```

## How to Use

1. Configure settings in `config.py` or via `.env` file (see `.env.example` at backend root)
2. Start the server:
   ```bash
   cd backend
   uv run fastapi dev main.py
   ```
3. The API will be available at `http://localhost:8000`
4. Interactive docs at `http://localhost:8000/docs`
