# Database Setup

PostgreSQL database infrastructure managed via Docker Compose.

## 🚀 Services

- **PostgreSQL**: Database server (port `5432`)
- **PgAdmin 4**: Web-based GUI for managing PostgreSQL (port `5050`)
- **PgHero**: Performance dashboard (port `8080`)

## 🛠️ Usage

1.  **Start Services**:
    ```bash
    docker-compose up -d
    ```

2.  **Access PgAdmin**:
    - URL: `http://localhost:5050`
    - Email: `admin@admin.com`
    - Password: `root`
    - **Add Server**:
        - Host: `db` (internal Docker network name)
        - Port: `5432`
        - User: `root`
        - Password: `root`

3.  **Access PgHero**:
    - URL: `http://localhost:8080`

4.  **Stop Services**:
    ```bash
    docker-compose down
    ```

## 📝 Configuration

Default credentials (hardcoded in `docker-compose.yaml` for local dev):
- DB Host: `localhost` (or `db` inside Docker network)
- DB Port: `5432`
- DB User: `root`
- DB Password: `root`
- DB Name: `test_db`
