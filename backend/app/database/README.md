# `database/` — PostgreSQL Connection & Table Models

This module manages the PostgreSQL database connection using SQLAlchemy and defines the table schema for storing scraped LinkedIn posts.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package initializer |
| `connection.py` | Database engine, session factory, table models, and init helper |

## How It Works

### Engine & Session

- The SQLAlchemy engine and `SessionLocal` session factory are **only created** when `STORE_IN_DB = True` in `app/config.py`.
- If DB storage is disabled, `engine` and `SessionLocal` remain `None` — no database connection is attempted.
- The connection URL is built from environment variables: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`.

### Table: `linkedin_posts`

| Column | Type | Description |
|---|---|---|
| `id` | `Integer` (PK) | Auto-incrementing primary key |
| `author` | `String(255)` | LinkedIn post author name |
| `timestamp` | `String(50)` | Relative timestamp (e.g., "2h", "3d") |
| `emails` | `Text` | Comma-separated emails extracted from the post |
| `contact_numbers` | `Text` | Comma-separated phone numbers |
| `apply_links` | `Text` | Comma-separated application URLs |
| `content` | `Text` | Full text content of the post |
| `content_hash` | `String(64)` | SHA-256 hash for deduplication (unique, indexed) |
| `created_at` | `DateTime` | UTC timestamp when the record was created |
| `batch_number` | `Integer` | Batch number from the Chrome extension session |

### Key Functions

| Function | Description |
|---|---|
| `init_db()` | Creates all tables if they don't exist. Called at app startup. |
| `get_db()` | FastAPI dependency that yields a DB session and ensures cleanup. |

## How to Use

1. **Enable DB storage** in `app/config.py`:
   ```python
   STORE_IN_DB = True
   ```

2. **Set database credentials** in `.env`:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=root
   DB_PASSWORD=root
   DB_NAME=test_db
   ```

3. **Start a PostgreSQL instance** (e.g., via Docker):
   ```bash
   docker run -d --name postgres \
     -e POSTGRES_USER=root \
     -e POSTGRES_PASSWORD=root \
     -e POSTGRES_DB=test_db \
     -p 5432:5432 postgres:16
   ```

4. Tables are **automatically created** when the FastAPI app starts.

## Dependencies

- `sqlalchemy` — ORM and database engine
- `app.config` — Database URL and feature toggles
