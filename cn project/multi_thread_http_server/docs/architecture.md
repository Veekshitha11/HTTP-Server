Thread Pool & Server Architecture


# Multi-threaded HTTP Server Architecture

## Overview
This document explains the architecture of the multi-threaded HTTP server implemented using Python socket programming. The server can handle multiple clients concurrently, process GET and POST requests, serve binary files, and ensure security against path traversal and host header attacks.

---

## 1. Server Components

### 1.1 Server (`server.py`)
- Listens on a configurable host and port (default: `127.0.0.1:8080`).
- Accepts incoming TCP connections.
- Delegates requests to the thread pool for concurrent processing.
- Maintains socket lifecycle for persistent and non-persistent connections.
- Implements connection timeout and max requests per connection.

### 1.2 Thread Pool (`thread_pool.py`)
- Pre-spawns a configurable number of worker threads (default: 10).
- Uses a queue to hold pending connections when all threads are busy.
- Threads fetch tasks from the queue and handle them independently.
- Synchronization is done via locks to ensure thread safety.
- Logs thread activity, queuing, and dequeuing of client connections.

### 1.3 Request Handler (`request_handler.py`)
- Parses HTTP requests (GET, POST).
- Validates HTTP format, headers, and Host field.
- Dispatches GET requests to static or binary file serving.
- Dispatches POST requests to JSON upload processing.
- Generates HTTP responses with proper status codes and headers.

### 1.4 Utilities (`utils.py`)
- Provides helper functions:
  - Date formatting in RFC 7231 format.
  - MIME type detection for files.
  - Path validation to prevent directory traversal.
  - Logging with timestamps.
  - Random ID generation for uploaded files.

---

## 2. Connection Management
- Supports `Connection: keep-alive` for persistent connections.
- Implements idle timeout of 30 seconds.
- Limits maximum 100 requests per persistent connection.
- Closes connections gracefully on timeout or max request limit.

---

## 3. Security Measures
- **Path Traversal Protection:** Blocks requests with `..`, `./`, or absolute paths.
- **Host Header Validation:** Accepts only requests where Host matches server address.
- Returns `403 Forbidden` or `400 Bad Request` for invalid access attempts.
- Logs all security violations.

---

## 4. Thread Pool Flow

Incoming TCP Connection
│
▼
Server accepts socket
│
▼
Task queued
│
▼
Thread pool assigns
│
▼
Request Handler processes
(GET / POST / Error)
│
▼
Response sent to client
│
▼
Connection closed or kept alive


---

## 5. Logging
- Logs include:
  - Thread handling each connection.
  - Request type and path.
  - Host validation status.
  - File transfer details (binary or HTML).
  - Response status codes.
  - Thread pool saturation and queue events.

---

**End of Architecture Document**
