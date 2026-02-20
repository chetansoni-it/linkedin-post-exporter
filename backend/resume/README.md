# `resume/` — Resume Attachments

This directory contains the resume file(s) that are **automatically attached** to every outgoing email sent by the backend.

## How It Works

- When an email is sent (via `POST /send-emails` or `POST /trigger-emails`), the backend scans this directory and attaches **all files** found.
- Supported formats: **PDF, DOCX**, or any other file type — all files in this directory will be attached.
- The backend uses `os.listdir()` to discover files, so simply drop your resume here.

## Current Contents

| File | Description |
|---|---|
| `CHETAN SONI Resume DevOps.pdf` | Resume file attached to outgoing emails |

## Configuration

In `app/config.py`:

```python
ATTACHMENT_DIR = "resume/"    # Path to this directory (relative to backend/)
```

## How to Use

1. **Add your resume**: Place your resume PDF or DOCX file in this directory.
2. **Multiple files**: You can add multiple files — all will be attached to every email.
3. **Update resume**: Simply replace the file(s) in this directory with your updated version.
4. **No resume**: If this directory is empty, emails will be sent without attachments (a warning will be logged).

## ⚠️ Important

- Keep file sizes reasonable — large attachments may cause SMTP delivery issues.
- File names are preserved as-is in the email attachment — use professional naming conventions.
- This directory should **not** be committed to version control if it contains personal documents.
