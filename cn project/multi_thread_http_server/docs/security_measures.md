# Security Measures in Multi-threaded HTTP Server

This document describes the security measures implemented in the HTTP server to protect against common attacks and ensure safe operation.

---

## 1. Path Traversal Protection
- Server validates all requested paths.
- Blocks any paths containing:
  - `..` (parent directory traversal)
  - `./` (current directory tricks)
  - Absolute paths (e.g., `/etc/passwd`)
- Unauthorized paths return `403 Forbidden`.
- Ensures all file accesses remain within the `resources/` directory.

---

## 2. Host Header Validation
- Server checks the `Host` header of each request.
- Only allows requests where `Host` matches the server’s host and port:
  - e.g., `localhost:8080` or `127.0.0.1:8080`
- Missing Host header → `400 Bad Request`
- Mismatched Host header → `403 Forbidden`
- Violations are logged for monitoring.

---

## 3. Method Restrictions
- Only **GET** and **POST** methods are allowed.
- Any other HTTP method (PUT, DELETE, PATCH, etc.) returns `405 Method Not Allowed`.

---

## 4. Content-Type Validation
- POST requests only accept `application/json`.
- Non-JSON content → `415 Unsupported Media Type`
- Invalid JSON → `400 Bad Request`

---

## 5. Connection Management Security
- Persistent connections are limited to **100 requests** to prevent abuse.
- Idle connections timeout after **30 seconds**.
- Properly closes connections to avoid resource leaks.

---

## 6. Logging for Monitoring
- Logs all:
  - Security violations (path traversal, host mismatch)
  - File access attempts
  - Unauthorized method usage
- Helps in monitoring attacks and debugging security issues.

---

## 7. Future Security Considerations
- Implement SSL/TLS for encrypted communication.
- Add authentication and authorization for sensitive files.
- Rate limiting to prevent denial-of-service attacks.
- Log rotation and alerting for critical security events.

---

**End of Security Measures Document**
