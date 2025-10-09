# Binary File Transfer in Multi-threaded HTTP Server

## Overview
This document explains how the server handles **binary file transfer** for GET requests, ensuring file integrity and proper browser behavior.

---

## 1. Supported File Types
- `.png` → `application/octet-stream`
- `.jpg` / `.jpeg` → `application/octet-stream`
- `.txt` → `application/octet-stream` (download)
- `.html` → `text/html; charset=utf-8` (render in browser)
- Any other types → `415 Unsupported Media Type`

---

## 2. File Handling Process

1. **Request Parsing**
   - Server parses GET request path.
   - Maps requested path to `resources/` folder.
   - Validates path to prevent traversal attacks.

2. **Binary Reading**
   - Files are opened in binary mode (`rb`).
   - Buffered read (4KB or 8KB chunks) is used for large files.

3. **Response Headers**
   - `HTTP/1.1 200 OK`
   - `Content-Type: application/octet-stream`
   - `Content-Length: [file size in bytes]`
   - `Content-Disposition: attachment; filename="[filename]"`
   - `Date: [current date RFC 7231]`
   - `Server: Multi-threaded HTTP Server`
   - `Connection: keep-alive/close`

4. **Data Transfer**
   - Entire file content is sent over TCP socket.
   - Chunked reading prevents memory overflow for large files.
   - Browser prompts user to download `.png`, `.jpg`, `.txt` files.

---

## 3. Error Handling
- **File Not Found:** `404 Not Found`
- **Unsupported File Type:** `415 Unsupported Media Type`
- **Unauthorized Access:** `403 Forbidden` for invalid paths

---

## 4. Logging
- Each binary transfer logs:
  - Thread name
  - Client IP and port
  - File name and size
  - Status of transfer (`200 OK`)
  - Connection type (`keep-alive` or `close`)

Example:

[2025-10-10 12:15:30] [Thread-2] Connection from 127.0.0.1:54321
[2025-10-10 12:15:30] [Thread-2] GET /logo.png
[2025-10-10 12:15:30] Sending binary file: logo.png (234567 bytes)
[2025-10-10 12:15:30] Response: 200 OK (234567 bytes transferred)
[2025-10-10 12:15:30] Connection: keep-alive


---

## 5. Notes
- Files are sent as raw bytes to avoid corruption.
- `Content-Disposition: attachment` ensures browser download instead of rendering.
- Large files (>1MB) are handled efficiently using buffered reads.

---

**End of Binary Transfer Document**
