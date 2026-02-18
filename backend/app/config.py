"""
============================================
 Configuration File
 Change these values as needed.
============================================

This is the SINGLE source of truth for all storage and database settings.
Toggle STORE_IN_CSV and STORE_IN_DB to control where data is persisted.
"""

# ---- Storage Toggles ----
STORE_IN_CSV = True          # Set to True to save scraped data to CSV files
STORE_IN_DB = False           # Set to True to save scraped data to PostgreSQL

# ---- CSV Settings ----
CSV_DIR = "data"                                # Directory for CSV files (relative to backend/)
CSV_POSTS_FILE = "linkedin_posts.csv"           # Filename for scraped LinkedIn posts
CSV_EMAIL_STATUS_FILE = "email_status.csv"      # Filename for email delivery statuses

# ---- PostgreSQL Settings (matches ./db/docker-compose.yaml) ----
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "test_db"

# Constructed database URL for SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---- API Settings ----
API_HOST = "0.0.0.0"
API_PORT = 8000
