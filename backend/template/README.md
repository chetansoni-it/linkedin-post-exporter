# `template/` — Email Templates

This directory contains the email template used for all outgoing emails sent by the backend.

## Files

| File | Description |
|---|---|
| `email_body.txt` | Email subject (line 1) and body (remaining lines) |

## Template Format

The template file follows a simple convention:

```
Subject: Your Subject Line Here

Body of the email starts here.
It can span multiple lines.

Best regards,
Your Name
```

- **Line 1**: Must start with `Subject:` followed by the email subject
- **Line 2+**: The email body (plain text)

## Current Template

The default template is configured for a DevOps/Cloud Solution Architect job application:

```
Subject: Resume - DevOps/Cloud Solution Architect - Chetan Soni

Greetings Recruitment Team,

I am writing regarding the DevOps/Cloud Solution Architect position...
```

## What Gets Added Automatically

The backend **appends** the following to the email body automatically (you don't need to include these in the template):

1. **Portfolio link** — if `PORTFOLIO_LINK` is set in `.env`
2. **LinkedIn post reference** — author name, post content, contact numbers, and apply links from the original LinkedIn post

## Configuration

In `app/config.py`:

```python
TEMPLATE_FILE = "template/email_body.txt"    # Path to this file
```

## How to Use

1. **Edit the template**: Open `email_body.txt` and modify the subject and body to match your needs.
2. **Keep line 1 as subject**: The first line is always parsed as the email subject.
3. **Plain text only**: The email is sent as plain text (`text/plain`), not HTML.
4. **Restart not required**: The template is read fresh on every email send — changes take effect immediately.

## ⚠️ Important

- Do **not** delete this file — the email service will fail if the template is missing.
- The `Subject:` prefix on line 1 is automatically stripped — don't include it twice.
