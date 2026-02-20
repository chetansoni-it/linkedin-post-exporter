# `storage/` — Storage Backend Implementations

This module provides the low-level storage operations for both CSV and PostgreSQL backends. The higher-level orchestration (deciding which backend to use, deduplication priority) is handled by `app/services/storage.py`.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Package initializer |
| `csv_storage.py` | CSV file operations — read, write, hash, and deduplicate |
| `db_storage.py` | PostgreSQL operations via SQLAlchemy — read, write, and deduplicate |

---

## `csv_storage.py` — CSV Backend

Stores LinkedIn posts in `data/linkedin_posts.csv`. This is the **default storage** backend.

### CSV Columns

```
author, timestamp, emails, contact_numbers, apply_links, content, content_hash, batch_number, created_at
```

### Key Functions

| Function | Description |
|---|---|
| `generate_content_hash(author, content)` | Creates SHA-256 hash from `author + content[:200]` for dedup |
| `get_existing_post_hashes()` | Returns a `set` of all `content_hash` values in the CSV |
| `is_post_duplicate(content_hash)` | Checks if a hash already exists |
| `save_posts(posts)` | Appends a list of post dicts to the CSV; returns row count |
| `get_all_posts()` | Reads all posts and returns them as a list of dicts |

### Auto-Setup

- The `data/` directory and CSV file are **created automatically** if they don't exist.
- Headers are written on first use.

---

## `db_storage.py` — PostgreSQL Backend

Stores LinkedIn posts in the `linkedin_posts` table using SQLAlchemy ORM.

### Key Functions

| Function | Description |
|---|---|
| `is_post_duplicate(db, content_hash)` | Checks if a hash exists in the DB |
| `save_posts(db, posts)` | Inserts a list of post dicts into the DB; returns row count |
| `get_all_posts(db)` | Reads all posts from DB and returns them as a list of dicts |

### Usage

Enable PostgreSQL storage in `app/config.py`:

```python
STORE_IN_DB = True
```

All `db_storage` functions require a SQLAlchemy `Session` parameter, which is provided automatically by the FastAPI dependency injection system (`get_db()` / `get_optional_db()`).

## How to Use

These modules are called by `app/services/storage.py`. Direct usage:

```python
from app.storage import csv_storage, db_storage

# CSV
hashes = csv_storage.get_existing_post_hashes()
csv_storage.save_posts([{"author": "...", "content": "...", ...}])

# DB (requires a session)
from app.database.connection import SessionLocal
db = SessionLocal()
db_storage.save_posts(db, [{"author": "...", "content": "...", ...}])
db.close()
```
