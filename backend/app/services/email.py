"""
Email sending service.

Ported from ./send-email/main.py into a clean, modular service.
Handles:
  - Reading subject/body from template/email_body.txt
  - Attaching files from resume/ directory
  - Sending via Gmail SMTP
  - Logging sent emails to sent-mails/sent-mails.csv
  - Duplicate/company-domain detection from sent-mails log
"""

import smtplib
import csv
import os
import re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from app.config import (
    SENDER_EMAIL,
    SENDER_PASSWORD,
    SMTP_SERVER,
    SMTP_PORT,
    PORTFOLIO_LINK,
    TEMPLATE_FILE,
    ATTACHMENT_DIR,
    SENT_EMAILS_FILE,
)


# Resolve paths relative to backend/ root
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# List of common public email providers — skip company-domain matching for these
COMMON_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com',
    'aol.com', 'protonmail.com', 'zoho.com', 'yandex.com', 'mail.com',
    'msn.com', 'live.com', 'me.com', 'googlemail.com', 'rocketmail.com',
    'btinternet.com', 'comcast.net', 'verizon.net', 'cox.net', 'att.net',
    'sbcglobal.net', 'bellsouth.net', 'charter.net', 'shaw.ca', 'earthlink.net',
    'mail.ru', 'gmx.com', 'gmx.de', 'web.de', 't-online.de', 'libero.it',
    'virgilio.it', 'alice.it', 'wanadoo.fr', 'orange.fr', 'free.fr', 'laposte.net',
    'rediffmail.com', 'indiatimes.com', 'tiscali.it', 'uol.com.br', 'bol.com.br',
    'terra.com.br', 'ig.com.br', 'globomail.com', 'oi.com.br', 'sky.com',
    'virginmedia.com', 'ntlworld.com', 'blueyonder.co.uk', 'talktalk.net',
}


# ========================
#  Helpers
# ========================

def _resolve(path: str) -> str:
    """Resolves a path relative to backend/ root."""
    return os.path.join(_BASE_DIR, path)


def get_base_domain(domain: str) -> str:
    """Gets base domain for comparison (e.g., mail.google.com → google.com)."""
    if not domain:
        return ""
    parts = domain.split('.')
    if len(parts) > 2:
        if parts[-2] in ('com', 'co', 'org', 'net', 'edu', 'gov', 'ac') and len(parts) >= 3:
            return '.'.join(parts[-3:])
        return '.'.join(parts[-2:])
    return domain


# ========================
#  Template & Attachments
# ========================

def read_template() -> tuple[str | None, str | None]:
    """Reads subject (line 1) and body (rest) from template/email_body.txt."""
    path = _resolve(TEMPLATE_FILE)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        subject, *body_lines = content.split('\n', 1)
        subject = subject.strip().replace("Subject:", "").strip()
        body = '\n'.join(body_lines).strip()
        return subject, body
    except FileNotFoundError:
        print(f"[Email] Error: Template not found at {path}")
        return None, None


def get_attachments() -> list[str]:
    """Returns list of file paths from resume/ directory."""
    directory = _resolve(ATTACHMENT_DIR)
    attachments = []
    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                attachments.append(filepath)
    except FileNotFoundError:
        print(f"[Email] Warning: Attachment directory not found at {directory}")
    return attachments


# ========================
#  Sent-Mails Log
# ========================

def get_sent_data() -> tuple[set[str], dict[str, list[str]]]:
    """
    Reads sent-mails CSV and returns:
      - set of already-sent email addresses
      - dict of {domain: [emails]} for company-domain matching
    """
    sent_file = _resolve(SENT_EMAILS_FILE)
    sent_emails: set[str] = set()
    sent_domains_map: dict[str, list[str]] = {}

    if not os.path.exists(sent_file):
        return sent_emails, sent_domains_map

    try:
        with open(sent_file, mode='r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            first_row = next(reader, None)
            if first_row and '@' in first_row[0]:
                _process_sent_row(first_row, sent_emails, sent_domains_map)
            for row in reader:
                _process_sent_row(row, sent_emails, sent_domains_map)
    except Exception as e:
        print(f"[Email] Warning: Could not read {sent_file}: {e}")

    return sent_emails, sent_domains_map


def _process_sent_row(row: list, sent_emails: set, sent_domains_map: dict):
    """Processes a single row from the sent-mails CSV."""
    if row and len(row) > 0:
        email = row[0].strip().lower()
        if email and '@' in email:
            sent_emails.add(email)
            domain = email.split('@')[-1]
            if domain and domain not in COMMON_DOMAINS:
                sent_domains_map.setdefault(domain, [])
                if email not in sent_domains_map[domain]:
                    sent_domains_map[domain].append(email)
                base = get_base_domain(domain)
                if base and base != domain:
                    sent_domains_map.setdefault(base, [])
                    if email not in sent_domains_map[base]:
                        sent_domains_map[base].append(email)


def log_sent_email(recipient: str, metadata: dict | None = None):
    """Appends a sent email record to sent-mails/sent-mails.csv."""
    sent_file = _resolve(SENT_EMAILS_FILE)
    os.makedirs(os.path.dirname(sent_file), exist_ok=True)

    file_exists = os.path.exists(sent_file)

    with open(sent_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists or os.path.getsize(sent_file) == 0:
            writer.writerow([
                'Recipient Email', 'Date Sent', 'Author',
                'Contact Numbers', 'Apply Links', 'Content',
            ])
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        author = metadata.get('author', '') if metadata else ''
        contact_numbers = metadata.get('contact_numbers', '') if metadata else ''
        apply_links = metadata.get('apply_links', '') if metadata else ''
        content = metadata.get('content', '') if metadata else ''
        writer.writerow([recipient, current_time, author, contact_numbers, apply_links, content])


# ========================
#  Email Composition
# ========================

def create_message(
    recipient_email: str,
    subject: str,
    body: str,
    attachments: list[str],
    metadata: dict | None = None,
) -> MIMEMultipart:
    """Creates the full email message with body, portfolio link, post reference, and attachments."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject

    full_body = body

    # Add portfolio link
    if PORTFOLIO_LINK:
        full_body += "\n\n" + "★" * 50
        full_body += f"\n\n📌 MY PORTFOLIO: {PORTFOLIO_LINK}\n"
        full_body += "★" * 50

    # Add LinkedIn post reference if available
    if metadata:
        full_body += "\n\n" + "=" * 50
        full_body += "\n[Reference - LinkedIn Post Details]"
        full_body += "\n" + "=" * 50
        if metadata.get('author'):
            full_body += f"\nPosted by: {metadata['author']}"
        if metadata.get('content'):
            full_body += f"\n\nPost Content:\n{metadata['content']}"
        if metadata.get('contact_numbers'):
            full_body += f"\n\nContact Numbers: {metadata['contact_numbers']}"
        if metadata.get('apply_links'):
            full_body += f"\n\nApply Links: {metadata['apply_links']}"
        full_body += "\n" + "=" * 50

    msg.attach(MIMEText(full_body, 'plain'))

    # Attach files from resume/ directory
    for filepath in attachments:
        try:
            part = MIMEBase('application', 'octet-stream')
            with open(filepath, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            filename = os.path.basename(filepath)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)
        except Exception as e:
            print(f"[Email] Could not attach {filepath}: {e}")

    return msg


# ========================
#  Send Logic
# ========================

def validate_email_config() -> str | None:
    """Returns an error message if email credentials are not set, else None."""
    if not SENDER_EMAIL:
        return "SENDER_EMAIL is not set in .env"
    if not SENDER_PASSWORD:
        return "SENDER_PASSWORD is not set in .env"
    return None


def check_duplicates(emails: list[str]) -> dict:
    """
    Checks a list of emails against sent-mails log.
    Returns:
      - clean: list of emails safe to send
      - duplicates: list of already-sent emails
      - company_matches: list of (email, previously_contacted_email) tuples
    """
    sent_emails, sent_domains_map = get_sent_data()

    clean = []
    duplicates = []
    company_matches = []

    for email in emails:
        email = email.strip().lower()
        if not email or '@' not in email:
            continue

        domain = email.split('@')[-1]
        base_domain = get_base_domain(domain)

        if email in sent_emails:
            duplicates.append(email)
        elif domain in sent_domains_map:
            company_matches.append({"email": email, "previous": sent_domains_map[domain][0]})
        elif base_domain and base_domain in sent_domains_map:
            company_matches.append({"email": email, "previous": sent_domains_map[base_domain][0]})
        else:
            clean.append(email)

    return {
        "clean": clean,
        "duplicates": duplicates,
        "company_matches": company_matches,
    }


def send_email_to_recipients(
    emails: list[str],
    metadata: dict | None = None,
    skip_duplicates: bool = True,
) -> dict:
    """
    Sends emails to the provided list of recipients.

    Args:
        emails: list of recipient email addresses
        metadata: optional LinkedIn post metadata (author, content, etc.)
        skip_duplicates: if True, skip already-contacted emails

    Returns a summary dict with success/failure counts.
    """
    # Validate config
    config_error = validate_email_config()
    if config_error:
        return {"error": config_error, "sent": 0, "failed": 0}

    # Read template
    subject, body = read_template()
    if not subject:
        return {"error": "Could not read email template from template/email_body.txt", "sent": 0, "failed": 0}

    # Get attachments
    attachments = get_attachments()

    # Dedup check
    if skip_duplicates:
        dedup = check_duplicates(emails)
        recipients = dedup["clean"]
        skipped_dupes = dedup["duplicates"]
        skipped_company = dedup["company_matches"]
    else:
        recipients = [e.strip().lower() for e in emails if e.strip() and '@' in e]
        skipped_dupes = []
        skipped_company = []

    if not recipients:
        return {
            "error": None,
            "message": "No new recipients to send to.",
            "sent": 0,
            "failed": 0,
            "duplicates_skipped": len(skipped_dupes),
            "company_matches_skipped": len(skipped_company),
        }

    # Send via SMTP
    sent_count = 0
    failed = []

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        for recipient in recipients:
            msg = create_message(recipient, subject, body, attachments, metadata)
            try:
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
                log_sent_email(recipient, metadata)
                sent_count += 1
                print(f"[Email] ✓ Sent to: {recipient}")
            except Exception as e:
                failed.append({"email": recipient, "error": str(e)})
                print(f"[Email] ✗ Failed to send to {recipient}: {e}")

        server.quit()
    except Exception as e:
        return {
            "error": f"SMTP connection failed: {str(e)}",
            "sent": sent_count,
            "failed": len(failed),
            "failed_details": failed,
        }

    return {
        "error": None,
        "message": f"Successfully sent {sent_count} email(s).",
        "sent": sent_count,
        "failed": len(failed),
        "failed_details": failed,
        "duplicates_skipped": len(skipped_dupes),
        "company_matches_skipped": len(skipped_company),
    }
