"""
============================================
 Configuration File
 Change these values as needed.
============================================

This is the SINGLE source of truth for all settings.
Secrets are loaded from .env file — never hardcode them here.
Toggle STORE_IN_CSV and STORE_IN_DB to control where data is persisted.
"""

import os
from dotenv import load_dotenv

# Load .env file from backend/ root
load_dotenv()

# ---- Storage Toggles ----
STORE_IN_CSV = True          # Set to True to save scraped data to CSV files
STORE_IN_DB = False          # Set to True to save scraped data to PostgreSQL

# ---- CSV Settings ----
CSV_DIR = "data"                                # Directory for CSV files (relative to backend/)
CSV_POSTS_FILE = "linkedin_posts.csv"           # Filename for scraped LinkedIn posts

# ---- PostgreSQL Settings (loaded from .env) ----
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "test_db")

# Constructed database URL for SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---- Email / SMTP Settings (loaded from .env) ----
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
PORTFOLIO_LINK = os.getenv("PORTFOLIO_LINK", "")

# ---- Email File Paths (relative to backend/) ----
TEMPLATE_FILE = "template/email_body.txt"       # Subject on line 1, body below
ATTACHMENT_DIR = "resume/"                       # Put your resume PDF/DOCX here
SENT_EMAILS_FILE = "sent-mails/sent-mails.csv"  # Log of sent emails

# ---- API Settings ----
API_HOST = "0.0.0.0"
API_PORT = 8000
