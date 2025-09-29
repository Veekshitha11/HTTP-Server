# Multi-threaded HTTP Server in Python

This project is a multi-threaded HTTP server built from scratch using Python's low-level socket programming. It is designed to handle multiple concurrent client connections, serve static and binary files, process JSON data via POST requests, and implement key HTTP security features.

---
## Folder Structure
project/
├── server.py
├── README.md
├── sample_data.json
└── resources/
├── index.html, about.html, ...
├── logo.png, photo.jpg, ...
├── sample.txt, ...
└── uploads/


## Build and Run Instructions

1.  Ensure you have Python 3 installed.
2.  Navigate to the project's root directory in your terminal.
3.  Run the server using the following command:
    ```bash
    python server.py [port] [host] [pool_size]
    ```
4.  **Arguments (Optional)**:
    -   `port`: The port to listen on (default: 8080).
    -   `host`: The host address to bind to (default: 127.0.0.1).
    -   `pool_size`: The number of worker threads in the pool (default: 10).

    **Example**: To run on port 8000, accessible from any IP, with 20 threads:
    `python server.py 8000 0.0.0.0 20`

---

## Description of Binary Transfer Implementation

To ensure files are transferred without corruption, especially non-text files like images, the server implements a specific binary transfer strategy.

-   **Binary Reading**: All files, regardless of type, are opened and read in binary mode (`'rb'`). This preserves the exact byte sequence of the file and prevents any data corruption that could occur from text encoding/decoding.
-   **Content-Type Header**: For any file type intended for download (e.g., `.txt`, `.png`, `.jpg`), the `Content-Type` header in the HTTP response is set to `application/octet-stream`.
-   **Content-Disposition Header**: A `Content-Disposition: attachment; filename="..."` header is also sent. This header is a directive that instructs the browser to download the file and save it to the user's disk, rather than attempting to render or display it in the browser window.

---

## Thread Pool Architecture Explanation

The server manages concurrency using a classic thread pool model to avoid the high overhead of creating a new thread for every single request.

-   **Main Thread**: The primary thread's sole responsibility is to listen for incoming TCP connections on the main server socket.
-   **Task Queue**: When a new connection is accepted, the main thread places the client socket object (along with other necessary server info) into a thread-safe `queue.Queue`. If all worker threads are busy, new connections will wait in this queue.
-   **Worker Threads**: A fixed number of worker threads, configurable at startup, are created when the server launches. These threads run in an infinite loop, waiting to pull a connection task from the queue. When a worker acquires a connection, it is responsible for handling the entire client session (including multiple requests if `Keep-Alive` is used) before returning to the queue to await the next task. This model ensures the server remains responsive and does not exhaust system resources under load.

---

## Security Measures Implemented

The server includes two critical security measures to protect against common web vulnerabilities.

-   **Path Traversal Protection**: All requested file paths are first canonicalized to an absolute path. The server then strictly verifies that this resolved path is contained within the designated `resources` web root directory. Any request containing `../` or other sequences that attempts to access a file or directory outside of this web root is immediately rejected with a `403 Forbidden` error.
-   **Host Header Validation**: The server inspects the `Host` header of every HTTP/1.1 request. This header is validated against the server's own known host and port. If the `Host` header is missing in an HTTP/1.1 request, a `400 Bad Request` is returned. If the header's value does not match the server's address, the request is rejected with a `403 Forbidden` error. This prevents a class of attacks where a request is routed to a server it was not intended for.

---

## Known Limitations

-   The server does not support HTTPS (SSL/TLS encryption). All traffic is sent over unencrypted HTTP.
-   Advanced HTTP features such as chunked transfer encoding and content compression are not implemented.
-   The server only supports GET and POST methods. Other methods like PUT, DELETE, etc., will be rejected.
-   Error pages are basic text and not user-friendly HTML pages.
