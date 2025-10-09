#!/usr/bin/env python3
"""
server.py
Multi-threaded HTTP server using low-level sockets and a thread pool.

Run:
    python3 server.py [port] [host] [max_threads]

Examples:
    python3 server.py
    python3 server.py 8000 0.0.0.0 20
"""

import socket
import threading
import queue
import os
import sys
import time
import datetime
import traceback
import json
import random
import string
from urllib.parse import unquote, urlparse

# -----------------------------
# Configuration / Defaults
# -----------------------------
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_MAX_THREADS = 10
LISTEN_BACKLOG = 50
CONN_QUEUE_MAX = 200
MAX_REQUEST_READ = 8192
FILE_READ_CHUNK = 8192
KEEP_ALIVE_TIMEOUT = 30
KEEP_ALIVE_MAX_REQUESTS = 100

# Paths inside multi_thread_http_server
# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "resources")
UPLOADS_DIR = os.path.join(RESOURCE_DIR, "uploads")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "server.log")

SUPPORTED_TEXT_TYPES = {".html": "text/html; charset=utf-8"}
SUPPORTED_BINARY = {".txt", ".png", ".jpg", ".jpeg"}
SERVER_NAME = "Multi-threaded HTTP Server"

# Ensure directories exist (uploads and logs)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# -----------------------------
# Logging Utilities
# -----------------------------
log_lock = threading.Lock()

def now_ts():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def rfc7231_date():
    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

def log(msg):
    line = f"[{now_ts()}] {msg}"
    with log_lock:
        print(line)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

# -----------------------------
# Thread Pool
# -----------------------------
class ThreadPool:
    def __init__(self, max_workers):
        self.max_workers = max_workers
        self.task_queue = queue.Queue(maxsize=CONN_QUEUE_MAX)
        self.workers = []
        self.active_workers_lock = threading.Lock()
        self.active_count = 0
        self._create_workers()

    def _create_workers(self):
        for i in range(self.max_workers):
            t = threading.Thread(target=self._worker_loop, name=f"Thread-{i+1}", daemon=True)
            t.start()
            self.workers.append(t)

    def _worker_loop(self):
        while True:
            try:
                client_sock, client_addr = self.task_queue.get()
                with self.active_workers_lock:
                    self.active_count += 1
                try:
                    handle_client_connection(client_sock, client_addr)
                except Exception as e:
                    log(f"[{threading.current_thread().name}] Exception: {e}\n{traceback.format_exc()}")
                finally:
                    try: client_sock.close()
                    except Exception: pass
                    with self.active_workers_lock:
                        self.active_count -= 1
                    self.task_queue.task_done()
            except Exception as e:
                log(f"[{threading.current_thread().name}] Worker loop error: {e}")
                time.sleep(0.1)

    def submit(self, client_sock, client_addr):
        try:
            self.task_queue.put_nowait((client_sock, client_addr))
            return True
        except queue.Full:
            return False

    def status(self):
        with self.active_workers_lock:
            return self.active_count, self.max_workers, self.task_queue.qsize()

# -----------------------------
# HTTP Helpers
# -----------------------------
def safe_join_resources(path):
    if not path:
        return None
    parsed = urlparse(path)
    clean_path = unquote(parsed.path)
    if ".." in clean_path or clean_path.startswith("//"):
        return None
    if clean_path.startswith("/"):
        clean_path = clean_path[1:]
    if clean_path == "":
        clean_path = "index.html"
    candidate = os.path.join(RESOURCE_DIR, clean_path)
    try:
        cand_real = os.path.realpath(candidate)
        res_real = os.path.realpath(RESOURCE_DIR)
        if not cand_real.startswith(res_real):
            return None
    except Exception:
        return None
    return cand_real

def valid_host_header(host_header, server_host, server_port):
    if not host_header:
        return False, 400
    host_header = host_header.strip()
    if ":" in host_header:
        host, port = host_header.split(":", 1)
        try:
            port = int(port)
        except Exception:
            return False, 400
    else:
        host = host_header
        port = server_port
    acceptable_hosts = set()
    acceptable_hosts.add(f"{server_host}:{server_port}")
    if server_host in ("127.0.0.1", "localhost"):
        acceptable_hosts.add(f"localhost:{server_port}")
        acceptable_hosts.add(f"127.0.0.1:{server_port}")
    if server_host == "0.0.0.0":
        acceptable_hosts.add(f"localhost:{server_port}")
        acceptable_hosts.add(f"127.0.0.1:{server_port}")
    if f"{host}:{port}" in acceptable_hosts:
        return True, f"{host}:{port}"
    else:
        return False, 403

def make_response(status_code, reason, headers=None, body=b""):
    status_line = f"HTTP/1.1 {status_code} {reason}\r\n"
    hdrs = headers or {}
    hdrs.setdefault("Date", rfc7231_date())
    hdrs.setdefault("Server", SERVER_NAME)
    if isinstance(body, str):
        body = body.encode("utf-8")
    hdrs.setdefault("Content-Length", str(len(body)))
    header_lines = "".join(f"{k}: {v}\r\n" for k,v in hdrs.items())
    resp = (status_line + header_lines + "\r\n").encode("utf-8") + body
    return resp

def send_error(sock, status_code, reason, extra_headers=None, body_text=None):
    body = body_text if body_text is not None else f"<html><body><h1>{status_code} {reason}</h1></body></html>"
    headers = {"Content-Type": "text/html; charset=utf-8"}
    if extra_headers: headers.update(extra_headers)
    resp = make_response(status_code, reason, headers, body)
    try: sock.sendall(resp)
    except Exception: pass

# -----------------------------
# Request Parsing
# -----------------------------
def recv_all(sock, timeout=1.0):
    sock.settimeout(timeout)
    data = b""
    try: data = sock.recv(MAX_REQUEST_READ)
    except socket.timeout: return b""
    except Exception: return b""
    return data

def parse_http_request(raw_bytes):
    try:
        raw_text = raw_bytes.decode("iso-8859-1")
    except Exception: return None
    parts = raw_text.split("\r\n\r\n", 1)
    head = parts[0]
    body = parts[1].encode("iso-8859-1") if len(parts) > 1 else b""
    lines = head.split("\r\n")
    if len(lines) < 1: return None
    try:
        method, path, version = lines[0].split()
    except ValueError: return None
    headers = {}
    for hdr in lines[1:]:
        if ":" in hdr:
            k, v = hdr.split(":", 1)
            headers[k.strip()] = v.strip()
    return {"method": method, "path": path, "version": version, "headers": headers, "body": body}

# -----------------------------
# Client Connection Handler
# -----------------------------
def handle_client_connection(client_sock, client_addr):
    thread_name = threading.current_thread().name
    remote_ip, remote_port = client_addr
    log(f"[{thread_name}] Connection from {remote_ip}:{remote_port}")
    client_sock.settimeout(KEEP_ALIVE_TIMEOUT)
    requests_handled = 0
    keep_alive = True

    while keep_alive:
        if requests_handled >= KEEP_ALIVE_MAX_REQUESTS:
            log(f"[{thread_name}] Max requests per connection reached")
            break
        try:
            raw = recv_all(client_sock, timeout=KEEP_ALIVE_TIMEOUT)
            if not raw: break
            if b"\r\n\r\n" not in raw:
                try: raw += client_sock.recv(4096)
                except Exception: pass
            req = parse_http_request(raw)
            if not req:
                log(f"[{thread_name}] Malformed request")
                send_error(client_sock, 400, "Bad Request")
                break
            method = req["method"]
            path = req["path"]
            version = req["version"]
            headers = req["headers"]
            body = req["body"]
            log(f"[{thread_name}] Request: {method} {path} {version}")

            # Host header validation
            ok, host_result = valid_host_header(headers.get("Host"), SERVER_HOST, SERVER_PORT)
            if not ok:
                send_error(client_sock, host_result, "Host header invalid")
                break

            conn_hdr = headers.get("Connection", "").lower()
            keep_alive = (conn_hdr != "close") if version == "HTTP/1.1" else (conn_hdr == "keep-alive")

            if method == "GET":
                handle_get(client_sock, thread_name, path, headers, keep_alive)
            elif method == "POST":
                # read full body based on Content-Length
                content_length = headers.get("Content-Length")
                if content_length:
                    try: expected = int(content_length)
                    except: send_error(client_sock, 400, "Bad Request"); break
                    remaining = expected - len(body)
                    while remaining > 0:
                        try:
                            chunk = client_sock.recv(min(4096, remaining))
                            if not chunk: break
                            body += chunk
                            remaining -= len(chunk)
                        except Exception: break
                handle_post(client_sock, thread_name, path, headers, body, keep_alive)
            else:
                send_error(client_sock, 405, "Method Not Allowed")

            requests_handled += 1
            if not keep_alive: break
        except socket.timeout:
            log(f"[{thread_name}] Connection timed out")
            break
        except Exception as e:
            log(f"[{thread_name}] Unexpected error: {e}\n{traceback.format_exc()}")
            try: send_error(client_sock, 500, "Internal Server Error")
            except Exception: pass
            break

    try: client_sock.shutdown(socket.SHUT_RDWR)
    except Exception: pass
    try: client_sock.close()
    except Exception: pass
    log(f"[{thread_name}] Connection closed for {remote_ip}:{remote_port}")

# -----------------------------
# GET and POST
# -----------------------------
def handle_get(sock, thread_name, path, headers, keep_alive):
    file_path = safe_join_resources(path)
    if file_path is None or not os.path.exists(file_path) or not os.path.isfile(file_path):
        send_error(sock, 404, "Not Found")
        return
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    try:
        if ext == ".html":
            with open(file_path, "rb") as f:
                content = f.read()
            headers_out = {
                "Content-Type": SUPPORTED_TEXT_TYPES[".html"],
                "Content-Length": str(len(content)),
                "Connection": "keep-alive" if keep_alive else "close",
                "Keep-Alive": f"timeout={KEEP_ALIVE_TIMEOUT}, max={KEEP_ALIVE_MAX_REQUESTS}",
            }
            resp = make_response(200, "OK", headers_out, content)
            sock.sendall(resp)
        elif ext in SUPPORTED_BINARY:
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            headers_out = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(file_size),
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Connection": "keep-alive" if keep_alive else "close",
            }
            sock.sendall(make_response(200, "OK", headers_out))
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(FILE_READ_CHUNK)
                    if not chunk: break
                    sock.sendall(chunk)
        else:
            send_error(sock, 415, "Unsupported Media Type")
    except Exception as e:
        log(f"[{thread_name}] GET error: {e}")
        send_error(sock, 500, "Internal Server Error")

def handle_post(sock, thread_name, path, headers, body_bytes, keep_alive):
    content_type = headers.get("Content-Type", "").split(";", 1)[0].strip()
    if content_type != "application/json":
        send_error(sock, 415, "Unsupported Media Type")
        return
    try:
        data = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        send_error(sock, 400, "Bad Request")
        return
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        rand_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        filename = f"upload_{timestamp}_{rand_id}.json"
        filepath_abs = os.path.join(UPLOADS_DIR, filename)
        with open(filepath_abs, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        resp_body = {
            "status": "success",
            "message": "File created successfully",
            "filepath": f"/uploads/{filename}"
        }
        body_bytes_out = json.dumps(resp_body).encode("utf-8")
        headers_out = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body_bytes_out)),
            "Connection": "keep-alive" if keep_alive else "close"
        }
        resp = make_response(201, "Created", headers_out, body_bytes_out)
        sock.sendall(resp)
    except Exception as e:
        log(f"[{thread_name}] POST error: {e}")
        send_error(sock, 500, "Internal Server Error")

# -----------------------------
# Server Main Loop
# -----------------------------
def start_server(bind_host, bind_port, max_threads):
    global SERVER_HOST, SERVER_PORT
    SERVER_HOST = bind_host
    SERVER_PORT = bind_port
    pool = ThreadPool(max_threads)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((bind_host, bind_port))
        server_sock.listen(LISTEN_BACKLOG)
        server_sock.setblocking(True)
        log(f"HTTP Server started on http://{bind_host}:{bind_port}")
        log(f"Thread pool size: {max_threads}")
        log(f"Serving files from '{RESOURCE_DIR}'")
        try:
            while True:
                try:
                    client_sock, client_addr = server_sock.accept()
                    accepted = pool.submit(client_sock, client_addr)
                    if not accepted:
                        headers = {"Retry-After": "5", "Content-Type": "text/html; charset=utf-8", "Connection": "close"}
                        body = "<html><body><h1>503 Service Unavailable</h1></body></html>"
                        client_sock.sendall(make_response(503, "Service Unavailable", headers, body))
                        client_sock.close()
                except Exception:
                    pass
        except KeyboardInterrupt:
            log("Shutdown requested by user.")
        except Exception as e:
            log(f"Main loop error: {e}\n{traceback.format_exc()}")

# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    port = DEFAULT_PORT
    host = DEFAULT_HOST
    max_threads = DEFAULT_MAX_THREADS
    argv = sys.argv[1:]
    try:
        if len(argv) >= 1: port = int(argv[0])
        if len(argv) >= 2: host = argv[1]
        if len(argv) >= 3: max_threads = int(argv[2])
    except Exception:
        print("Usage: python3 server.py [port] [host] [max_threads]")
        sys.exit(1)
    start_server(host, port, max_threads)
