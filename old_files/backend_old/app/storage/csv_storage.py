"""
CSV storage backend.

Handles reading, writing, and deduplication for LinkedIn posts
and email statuses stored in CSV files.
"""

import csv
import os
import hashlib
from datetime import datetime, timezone

from app.config import CSV_DIR, CSV_POSTS_FILE, CSV_EMAIL_STATUS_FILE


# ========================
#  Paths
# ========================

# Resolve paths relative to the backend/ root
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POSTS_CSV_PATH = os.path.join(_BASE_DIR, CSV_DIR, CSV_POSTS_FILE)
EMAIL_STATUS_CSV_PATH = os.path.join(_BASE_DIR, CSV_DIR, CSV_EMAIL_STATUS_FILE)

# CSV column headers
POSTS_HEADERS = [
    "author", "timestamp", "emails", "contact_numbers",
    "apply_links", "content", "content_hash", "batch_number", "created_at",
]

EMAIL_STATUS_HEADERS = [
    "recipient_email", "status", "author", "error_message", "updated_at",
]


# ========================
#  Helpers
# ========================

def _ensure_dir():
    """Creates the CSV data directory if it doesn't exist."""
    dir_path = os.path.join(_BASE_DIR, CSV_DIR)
    os.makedirs(dir_path, exist_ok=True)


def _ensure_file(filepath: str, headers: list[str]):
    """Creates the CSV file with headers if it doesn't exist or is empty."""
    _ensure_dir()
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


def generate_content_hash(author: str, content: str) -> str:
    """Generates a deterministic hash for deduplication.

    Uses author + first 200 chars of content to create a unique fingerprint,
    similar to the Chrome extension's dedup key (author + timestamp + content[:120]).
    We use a wider slice and drop timestamp for server-side reliability.
    """
    raw = f"{author.strip().lower()}|{content.strip()[:200].lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ========================
#  Posts — Read / Write / Check
# ========================

def get_existing_post_hashes() -> set[str]:
    """Reads all content_hash values from the CSV for dedup checks."""
    hashes = set()
    _ensure_file(POSTS_CSV_PATH, POSTS_HEADERS)

    try:
        with open(POSTS_CSV_PATH, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                h = row.get("content_hash", "").strip()
                if h:
                    hashes.add(h)
    except Exception as e:
        print(f"[CSV] Warning: Could not read {POSTS_CSV_PATH}: {e}")

    return hashes


def is_post_duplicate(content_hash: str) -> bool:
    """Checks whether a post with this hash already exists in the CSV."""
    return content_hash in get_existing_post_hashes()


def save_posts(posts: list[dict]) -> int:
    """Appends a list of post dicts to the CSV. Returns number of rows written."""
    _ensure_file(POSTS_CSV_PATH, POSTS_HEADERS)

    count = 0
    with open(POSTS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=POSTS_HEADERS)
        for post in posts:
            writer.writerow(post)
            count += 1

    return count


# ========================
#  Email Status — Read / Write / Check
# ========================

def get_existing_email_statuses() -> dict[str, str]:
    """Returns a dict of {recipient_email: status} from the CSV."""
    statuses: dict[str, str] = {}
    _ensure_file(EMAIL_STATUS_CSV_PATH, EMAIL_STATUS_HEADERS)

    try:
        with open(EMAIL_STATUS_CSV_PATH, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("recipient_email", "").strip().lower()
                if email:
                    statuses[email] = row.get("status", "")
    except Exception as e:
        print(f"[CSV] Warning: Could not read {EMAIL_STATUS_CSV_PATH}: {e}")

    return statuses


def save_email_status(data: dict) -> None:
    """Appends or updates an email status in the CSV.

    For simplicity, appends a new row. The latest row for a given email
    is considered the current status (last-write-wins).
    """
    _ensure_file(EMAIL_STATUS_CSV_PATH, EMAIL_STATUS_HEADERS)

    with open(EMAIL_STATUS_CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EMAIL_STATUS_HEADERS)
        writer.writerow(data)
