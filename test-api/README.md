# Test API

A simple catch-all FastAPI server for debugging and testing request payloads.

## 🚀 Features

- **Echoes Requests**: Prints all incoming HTTP requests (headers, body, params) to the console.
- **Universal Handler**: Catches any path/method.
- **CORS Enabled**: Accepts requests from any origin (useful for testing Chrome extensions).

## 🛠️ Usage

1.  **Run Server**:
    ```bash
    uv run fastapi dev main.py
    ```

    > **Note**: Runs on port `8000` by default. If the main backend is running, stop it first or run on a different port:
    ```bash
    uv run fastapi dev main.py --port 8001
    ```

2.  **Send Requests**:
    Example:
    ```bash
    curl -X POST http://localhost:8000/any/path -d '{"foo": "bar"}'
    ```

3.  **View Output**:
    Check your terminal to see the structured request details.
