# `sent-mails/` — Sent Email Log

This directory contains a CSV log of all emails successfully sent by the backend. It is used for **duplicate detection** and **company-domain matching** to prevent sending multiple emails to the same recipient or company.

## Files

| File | Description |
|---|---|
| `sent-mails.csv` | Log of every email successfully sent by the backend |

## CSV Format

| Column | Description |
|---|---|
| `Recipient Email` | The email address the message was sent to |
| `Date Sent` | Timestamp in `YYYY-MM-DD HH:MM:SS` format |
| `Author` | LinkedIn post author (for reference) |
| `Contact Numbers` | Contact numbers from the LinkedIn post |
| `Apply Links` | Application links from the LinkedIn post |
| `Content` | LinkedIn post content that triggered the email |

## How It Works

### Duplicate Detection

Before sending an email, the backend checks this log:

1. **Exact match**: If the recipient email was already sent to → **skipped**
2. **Company-domain match**: If someone at the same company domain (e.g., `@company.com`) was already contacted → **skipped**
3. **Public domains excluded**: Common providers (Gmail, Yahoo, Outlook, etc.) are excluded from company matching

### Logging

- Every successful email send appends a new row to this CSV.
- Failed sends are **not** logged here (they appear in the API response).
- The file and directory are **created automatically** on first email send.

## Configuration

In `app/config.py`:

```python
SENT_EMAILS_FILE = "sent-mails/sent-mails.csv"    # Path to this file
```

## How to Use

- **View history**: Open `sent-mails.csv` in any spreadsheet app or text editor.
- **Reset dedup**: To re-send emails to previously contacted recipients, delete or clear `sent-mails.csv`. It will be recreated on next send.
- **This file is auto-managed** — you don't need to edit it manually.

## ⚠️ Important

- Do **not** manually edit this file while the server is running — it may cause data corruption.
- This file should **not** be committed to version control — it contains real email addresses.
