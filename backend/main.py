from fastapi import FastAPI, Request
import json

app = FastAPI()

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def catch_all(request: Request, full_path: str):
    # Get request details
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    path_params = request.path_params
    client = request.client.host if request.client else None

    try:
        body = await request.body()
        body_content = body.decode("utf-8") if body else None
    except Exception:
        body_content = None

    # Print everything in terminal
    print("\n===== Incoming Request =====")
    print(f"Client IP: {client}")
    print(f"Method: {method}")
    print(f"Path: /{full_path}")
    print("Headers:")
    print(json.dumps(headers, indent=2))
    print("Query Params:")
    print(json.dumps(query_params, indent=2))
    print("Body:")
    print(body_content)
    print("============================\n")

    return {
        "status": "received",
        "method": method,
        "path": full_path
    }
