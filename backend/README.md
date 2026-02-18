# LinkedIn Post Exporter — Backend

FastAPI backend that receives scraped LinkedIn posts from the Chrome extension, stores them (CSV/PostgreSQL), and handles background email sending.

## 🚀 Features

- **Receive Data**: `POST /posts` endpoint for batch uploads.
- **Unified Storage**: Save to CSV (`backend/data/`) and/or PostgreSQL.
- **Smart Deduplication**: Prevents saving duplicate posts.
- **Background Email Job**: `POST /trigger-emails` sends emails in the background.
    - Reads from stored posts.
    - Deduplicates against `sent-mails/sent-mails.csv`.
    - Attaches resumes from `backend/resume/`.
- **Live Monitoring**: `GET /email-job-status` for real-time progress.

## 🛠️ Setup

1.  **Install Dependencies**:
    Using [uv](https://github.com/astral-sh/uv) (recommended):
    ```bash
    uv sync
    ```
    Or standard pip:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    Copy `.env.example` to `.env` and fill in your details:
    ```bash
    cp .env.example .env
    ```
    - **Database**: Set credentials if using PostgreSQL.
    - **Email**: Set Gmail App Password for sending emails.

3.  **Prepare Assets**:
    - **Resume**: converting your resume to PDF/DOCX and place it in `backend/resume/`.
    - **Email Template**: Edit `backend/template/email_body.txt` (Line 1 is Subject).

## ▶️ Running the Server

Start the development server:
```bash
uv run fastapi dev main.py
```
Server runs at `http://127.0.0.1:8000`.

## 📡 API Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/posts` | Receive a batch of scraped posts |
| `POST` | `/trigger-emails` | **Start the background email job** |
| `GET` | `/email-job-status` | Check job progress (sent/failed counts) |
| `POST` | `/send-emails` | Send to a specific list (manual) |
| `GET` | `/health` | Health check & storage status |

## 📂 Project Structure

- `app/`: Main application logic (routes, services, models).
- `data/`: CSV storage (auto-created).
- `resume/`: Place attachment files here.
- `sent-mails/`: Log of all sent emails.
- `template/`: Email subject and body template.
