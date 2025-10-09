# Multi-threaded HTTP Server

## Project Overview
This project implements a **multi-threaded HTTP server** from scratch using Python socket programming.  
The server can handle multiple concurrent clients, serve static HTML files, transfer binary content (images, text), and process JSON POST requests securely.  
It also implements various HTTP features including persistent connections, host validation, and connection timeouts.

---

## Features

- Multi-threaded architecture using a **thread pool** for concurrent request handling.
- Serves **HTML, PNG, JPEG, and TXT** files.
- Processes **JSON POST requests** and saves uploaded files to `resources/uploads/`.
- Implements **security measures**:
  - Path traversal protection
  - Host header validation
  - Method and content-type restrictions
- Supports **persistent connections** with configurable timeout and max requests per connection.
- Comprehensive logging of requests, responses, and thread activity.

---

## Folder Structure

project/
├── server.py # Main server file
├── thread_pool.py # Thread pool implementation
├── request_handler.py # HTTP request parsing and processing
├── utils.py # Utility functions (logging, MIME types, etc.)
├── requirements.txt # Dependencies (if any)
├── resources/ # Folder containing static files
│ ├── index.html
│ ├── about.html
│ ├── contact.html
│ ├── sample.txt
│ ├── logo.png
│ ├── photo.png
| ├── family.jpg
| ├── friend.jpg
│ └── uploads/ # JSON uploads from POST requests
└── tests/
├── test_get_requests.sh
├── test_post_requests.sh
├── test_security.sh
└── test_concurrency.py



---

## Build & Run Instructions

1. **Install Python 3.10+** on your system.
2. Clone the repository:

```bash
git clone <your-repo-link>
cd multi_thread_http_server



Install dependencies
pip install -r requirements.txt


Run the server (default port 8080):
python server.py


Open browser and navigate to:
http://localhost:8080


Access static HTML files (/about.html, /contact.html)

Download binary files (/logo.png, /photo.png, /sample.txt)



Binary File Transfer

Files are read in binary mode with buffered chunks for large files.

Headers include:
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Length: [file size]
Content-Disposition: attachment; filename="[filename]"
Date: [RFC 7231 formatted date]
Server: Multi-threaded HTTP Server
Connection: keep-alive/close

Browser prompts file download instead of rendering.


Security Measures

Path Traversal Protection: Blocks .., ./, and absolute paths.

Host Header Validation: Only allows requests with correct Host.

Method Restrictions: Only GET and POST allowed.

Content-Type Validation: Only application/json for POST.

Connection Limits: Prevents abuse via max requests and timeout.


Limitations

Supports only GET and POST methods.

Limited file types: .html, .txt, .png, .jpg/.jpeg.

No SSL/TLS (HTTP only, plain text).

Single-process multi-threaded, not distributed.

No authentication or advanced rate limiting.

Logging is synchronous and may slow under heavy load.




Testing
GET Requests

GET / → Serves index.html

GET /about.html → Serves about page

GET /logo.png → Downloads PNG file

GET /photo.png → Downloads PNG file

GET /sample.txt → Downloads text file

GET /nonexistent.png → 404 Not Found

POST Requests

POST /upload with valid JSON → Creates file in uploads/ and returns 201

POST /upload with non-JSON → 415 Unsupported Media Type

Security Tests

Path traversal attempts → 403 Forbidden

Missing or invalid Host header → 400 or 403

Concurrency Tests

Multiple clients handled simultaneously

Queued connections when thread pool is saturated

Note: Use test_get_requests.sh, test_post_requests.sh, test_security.sh, and test_concurrency.py for automated testing. On Windows, you can convert .sh scripts to .ps1 for PowerShell.

Logging

Logs contain timestamps, thread name, client IP/port, request type, and file transfer details.

Thread pool status and connection queue events are also logged.

Helps in monitoring server activity and security violations.

