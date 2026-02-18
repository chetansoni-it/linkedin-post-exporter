"""
Background email job runner.

Triggered by POST /trigger-emails. Runs as a background thread so the
API responds immediately while emails are sent in parallel.

Flow:
  1. Reads all stored posts from CSV or DB (whichever is configured)
  2. Extracts individual email addresses from each post's `emails` field
  3. Deduplicates against sent-mails/sent-mails.csv
  4. Sends emails one-by-one via Gmail SMTP with resume attached
  5. Updates job status in real-time (queryable via GET /email-job-status)
"""

import threading
from datetime import datetime, timezone

from app.config import STORE_IN_DB, STORE_IN_CSV
from app.storage import csv_storage
from app.storage import db_storage
from app.database.connection import SessionLocal
from app.services.email import (
    validate_email_config,
    check_duplicates,
    read_template,
    get_attachments,
    create_message,
    log_sent_email,
    SENDER_EMAIL,
    SENDER_PASSWORD,
    SMTP_SERVER,
    SMTP_PORT,
)

import smtplib


# ========================
#  Job Status Tracker
# ========================

_current_job: dict | None = None
_job_lock = threading.Lock()


def get_job_status() -> dict | None:
    """Returns the current (or last) job status."""
    with _job_lock:
        return dict(_current_job) if _current_job else None


def _update_job(updates: dict):
    """Thread-safe update to the job status dict."""
    with _job_lock:
        if _current_job is not None:
            _current_job.update(updates)


def is_job_running() -> bool:
    """Returns True if a job is currently in progress."""
    with _job_lock:
        return _current_job is not None and _current_job.get("status") == "running"


# ========================
#  Extract Emails from Posts
# ========================

def _extract_email_post_pairs(posts: list[dict]) -> list[dict]:
    """
    Extracts individual email addresses from each post's `emails` field.
    Returns a list of {email, metadata} pairs for sending.
    Each email gets the post's metadata attached so it shows in the email body.
    """
    pairs = []
    seen_emails = set()

    for post in posts:
        raw_emails = post.get("emails", "")
        if not raw_emails or not raw_emails.strip():
            continue

        # Split comma-separated emails
        email_list = [e.strip().lower() for e in raw_emails.split(",") if e.strip()]

        metadata = {
            "author": post.get("author", ""),
            "content": post.get("content", ""),
            "contact_numbers": post.get("contact_numbers", ""),
            "apply_links": post.get("apply_links", ""),
        }

        for email in email_list:
            if "@" in email and email not in seen_emails:
                seen_emails.add(email)
                pairs.append({"email": email, "metadata": metadata})

    return pairs


# ========================
#  Background Job Thread
# ========================

def _run_email_job():
    """
    The actual background worker. Reads posts from storage,
    extracts emails, deduplicates, sends emails, updates job status.
    """
    global _current_job

    try:
        # Step 1: Read all posts from the active storage
        _update_job({"phase": "reading_posts"})
        print("[EmailJob] Reading stored posts...")

        posts = []
        if STORE_IN_DB:
            try:
                db = SessionLocal()
                posts = db_storage.get_all_posts(db)
                db.close()
                print(f"[EmailJob] Read {len(posts)} posts from database.")
            except Exception as e:
                print(f"[EmailJob] DB read failed: {e}. Falling back to CSV.")
                posts = csv_storage.get_all_posts()
        elif STORE_IN_CSV:
            posts = csv_storage.get_all_posts()
            print(f"[EmailJob] Read {len(posts)} posts from CSV.")

        if not posts:
            _update_job({
                "status": "completed",
                "phase": "done",
                "message": "No posts found in storage. Scrape some LinkedIn posts first.",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            return

        # Step 2: Extract email-metadata pairs
        _update_job({"phase": "extracting_emails"})
        pairs = _extract_email_post_pairs(posts)
        total_emails_found = len(pairs)
        print(f"[EmailJob] Found {total_emails_found} unique emails across {len(posts)} posts.")

        if not pairs:
            _update_job({
                "status": "completed",
                "phase": "done",
                "message": "No emails found in stored posts.",
                "total_emails_found": 0,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            return

        # Step 3: Deduplicate against sent-mails
        _update_job({"phase": "deduplicating"})
        all_emails = [p["email"] for p in pairs]
        dedup = check_duplicates(all_emails)
        clean_emails = set(dedup["clean"])
        duplicates_skipped = len(dedup["duplicates"])
        company_matches_skipped = len(dedup["company_matches"])

        # Filter pairs to only clean emails
        pairs_to_send = [p for p in pairs if p["email"] in clean_emails]
        print(f"[EmailJob] After dedup: {len(pairs_to_send)} to send, "
              f"{duplicates_skipped} duplicates skipped, "
              f"{company_matches_skipped} company matches skipped.")

        _update_job({
            "total_emails_found": total_emails_found,
            "total_to_send": len(pairs_to_send),
            "duplicates_skipped": duplicates_skipped,
            "company_matches_skipped": company_matches_skipped,
        })

        if not pairs_to_send:
            _update_job({
                "status": "completed",
                "phase": "done",
                "message": "All emails already sent. No new recipients.",
                "sent": 0,
                "failed": 0,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            return

        # Step 4: Read template and attachments
        subject, body = read_template()
        if not subject or not body:
            _update_job({
                "status": "failed",
                "phase": "done",
                "message": "Could not read email template from template/email_body.txt",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            return

        attachments = get_attachments()

        # Step 5: Send emails via SMTP
        _update_job({"phase": "sending"})
        sent_count = 0
        failed_list = []

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for i, pair in enumerate(pairs_to_send):
                recipient = pair["email"]
                metadata = pair["metadata"]

                _update_job({
                    "current": i + 1,
                    "current_email": recipient,
                })

                try:
                    msg = create_message(recipient, subject, body, attachments, metadata)
                    server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
                    log_sent_email(recipient, metadata)
                    sent_count += 1
                    _update_job({"sent": sent_count})
                    print(f"[EmailJob] ✓ [{i+1}/{len(pairs_to_send)}] Sent to: {recipient}")
                except Exception as e:
                    failed_list.append({"email": recipient, "error": str(e)})
                    _update_job({"failed": len(failed_list)})
                    print(f"[EmailJob] ✗ [{i+1}/{len(pairs_to_send)}] Failed: {recipient} — {e}")

            server.quit()
        except Exception as e:
            _update_job({
                "status": "failed",
                "phase": "done",
                "message": f"SMTP connection failed: {str(e)}",
                "sent": sent_count,
                "failed": len(failed_list),
                "failed_details": failed_list,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
            print(f"[EmailJob] ✗ SMTP connection failed: {e}")
            return

        # Done!
        _update_job({
            "status": "completed",
            "phase": "done",
            "message": f"Job complete. Sent {sent_count} email(s), {len(failed_list)} failed.",
            "sent": sent_count,
            "failed": len(failed_list),
            "failed_details": failed_list,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        print(f"[EmailJob] ✓ Job complete: {sent_count} sent, {len(failed_list)} failed.")

    except Exception as e:
        _update_job({
            "status": "failed",
            "phase": "done",
            "message": f"Unexpected error: {str(e)}",
            "finished_at": datetime.now(timezone.utc).isoformat(),
        })
        print(f"[EmailJob] ✗ Unexpected error: {e}")


# ========================
#  Public Trigger
# ========================

def trigger_email_job() -> dict:
    """
    Starts the background email job.
    Returns immediately with a response while emails are sent in a thread.
    """
    global _current_job

    # Pre-flight checks
    config_error = validate_email_config()
    if config_error:
        return {"error": config_error}

    if not STORE_IN_CSV and not STORE_IN_DB:
        return {"error": "No storage backend enabled. Enable STORE_IN_CSV or STORE_IN_DB in config."}

    if is_job_running():
        return {"error": "An email job is already running. Check GET /email-job-status for progress."}

    # Initialize job status
    with _job_lock:
        _current_job = {
            "status": "running",
            "phase": "starting",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "message": "Email job started.",
            "total_emails_found": 0,
            "total_to_send": 0,
            "duplicates_skipped": 0,
            "company_matches_skipped": 0,
            "sent": 0,
            "failed": 0,
            "failed_details": [],
            "current": 0,
            "current_email": "",
        }

    # Launch background thread
    thread = threading.Thread(target=_run_email_job, daemon=True)
    thread.start()

    return {"error": None, "message": "Email job started in background. Check GET /email-job-status for progress."}
