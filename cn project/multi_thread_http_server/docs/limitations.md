# Limitations of Multi-threaded HTTP Server

This document outlines the known limitations of the current implementation of the multi-threaded HTTP server.

---

## 1. Performance
- The server uses a **fixed-size thread pool**, which may limit performance under extremely high load.
- For very large numbers of concurrent clients, the connection queue may grow and cause delays.

## 2. Supported Methods
- Only **GET** and **POST** requests are supported.
- Other HTTP methods like **PUT**, **DELETE**, **PATCH**, etc., return `405 Method Not Allowed`.

## 3. File Handling
- Only specific file types are supported:
  - `.html`, `.txt`, `.png`, `.jpg` / `.jpeg`
- Other file types return `415 Unsupported Media Type`.
- No support for serving dynamic content or scripts (e.g., PHP, CGI).

## 4. Connection Management
- Maximum 100 requests per persistent connection is enforced.
- Idle connections timeout after 30 seconds.
- The server does not implement advanced connection throttling or rate limiting.

## 5. Security
- Host header validation only allows exact match with the server address.
- No SSL/TLS encryption; all data is transmitted in plain HTTP.
- Does not support authentication or user permissions.

## 6. Scalability
- Single-process, multi-threaded design.
- Does not support distributed or load-balanced deployments.
- Not optimized for extremely large file transfers or high-throughput scenarios.

## 7. Logging
- Logging is synchronous and may slightly affect performance under heavy load.
- No log rotation implemented; large logs may accumulate over time.

---

**End of Limitations Document**
