import os
import datetime
import json
import threading

# --------------------------------------------------------------------
# 🧠 Timestamp Helpers
# --------------------------------------------------------------------
def rfc_7231_date():
    """
    Returns the current date in RFC 7231 format.
    Example: Tue, 15 Oct 2025 10:30:00 GMT
    """
    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")


def timestamp():
    """
    Simple timestamp for logging (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------
# 🧾 Logging Helper
# --------------------------------------------------------------------
def log(message):
    """
    Thread-safe console logging with timestamps and thread names.
    """
    thread_name = threading.current_thread().name
    print(f"[{timestamp()}] [{thread_name}] {message}")


# --------------------------------------------------------------------
# 📁 File and Path Utilities
# --------------------------------------------------------------------
def get_content_type(file_path):
    """
    Returns appropriate Content-Type based on file extension.
    """
    if file_path.endswith(".html"):
        return "text/html; charset=utf-8"
    elif file_path.endswith(".txt"):
        return "application/octet-stream"
    elif file_path.endswith(".png"):
        return "application/octet-stream"
    elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
        return "application/octet-stream"
    else:
        return None  # Unsupported file type


def is_path_secure(base_dir, requested_path):
    """
    Prevents path traversal attacks.
    Ensures the final resolved path is still within the base directory.
    """
    full_path = os.path.realpath(os.path.join(base_dir, requested_path.strip("/")))
    base_dir = os.path.realpath(base_dir)
    return full_path.startswith(base_dir)


def resolve_requested_path(base_dir, requested_path):
    """
    Safely resolves requested file path relative to the resources directory.
    Returns full path if safe, otherwise None.
    """
    if ".." in requested_path or requested_path.startswith(("/", "./", "../")):
        return None
    full_path = os.path.join(base_dir, requested_path.lstrip("/"))
    if os.path.isdir(full_path):
        full_path = os.path.join(full_path, "index.html")
    if not is_path_secure(base_dir, full_path):
        return None
    return full_path


# --------------------------------------------------------------------
# 🔐 JSON Helpers
# --------------------------------------------------------------------
def validate_json(content):
    """
    Validates JSON string and returns parsed dict if valid, else None.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------
# ⚙️ Misc Helpers
# --------------------------------------------------------------------
def build_response(status_code, headers, body=b""):
    """
    Builds a raw HTTP response in bytes format.
    `body` can be bytes (for binary) or str (for text).
    """
    reason_phrases = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        415: "Unsupported Media Type",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    reason = reason_phrases.get(status_code, "Unknown")

    if isinstance(body, str):
        body = body.encode("utf-8")

    header_lines = [f"HTTP/1.1 {status_code} {reason}"]
    for key, value in headers.items():
        header_lines.append(f"{key}: {value}")
    header_lines.append("")  # blank line
    header_lines.append("")  # for separation
    header_text = "\r\n".join(header_lines).encode("utf-8")

    return header_text + body
