import socket
import os
import threading
import queue
import sys
import json
from datetime import datetime
import uuid
import email.utils

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 8080
RESOURCES_DIR = 'resources'
UPLOADS_DIR = os.path.join(RESOURCES_DIR, 'uploads')
MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.txt': 'application/octet-stream',
    '.png': 'application/octet-stream',
    '.jpg': 'application/octet-stream',
    '.jpeg': 'application/octet-stream',
}

# --- Helper Functions ---
def build_response(status_code, status_message, headers=None, body=b''):
    final_headers = {
        'Date': email.utils.formatdate(usegmt=True),
        'Server': 'Multi-threaded HTTP Server',
    }
    if headers:
        final_headers.update(headers)

    response_line = f"HTTP/1.1 {status_code} {status_message}\r\n"
    response_headers = ""
    for key, value in final_headers.items():
        response_headers += f"{key}: {value}\r\n"
    
    return response_line.encode('utf-8') + response_headers.encode('utf-8') + b"\r\n" + body

# --- Request Handlers ---
def handle_get_request(request_path, response_headers):
    if request_path == '/':
        request_path = '/index.html'
    
    safe_base_path = os.path.abspath(RESOURCES_DIR)
    requested_file_path = os.path.normpath(os.path.join(safe_base_path, request_path.lstrip('/')))

    if not requested_file_path.startswith(safe_base_path):
        return build_response(403, "Forbidden", body=b"<h1>403 Forbidden</h1>")

    if not os.path.exists(requested_file_path) or not os.path.isfile(requested_file_path):
        return build_response(404, "Not Found", body=b"<h1>404 Not Found</h1>")

    _, file_extension = os.path.splitext(requested_file_path)
    content_type = MIME_TYPES.get(file_extension.lower(), 'application/octet-stream')
    
    with open(requested_file_path, 'rb') as f:
        file_content = f.read()

    response_headers['Content-Type'] = content_type
    response_headers['Content-Length'] = str(len(file_content))
    
    if content_type == 'application/octet-stream':
        filename = os.path.basename(requested_file_path)
        response_headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    return build_response(200, "OK", response_headers, file_content)

def handle_post_request(headers, body_data, response_headers):
    content_type = headers.get('content-type')
    if not content_type or "application/json" not in content_type:
        return build_response(415, "Unsupported Media Type", body=b"<h1>415 Unsupported Media Type</h1>")

    try:
        json_data = json.loads(body_data)
    except json.JSONDecodeError:
        return build_response(400, "Bad Request", body=b"<h1>400 Bad Request: Invalid JSON</h1>")

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_id = uuid.uuid4().hex[:6]
        filename = f"upload_{timestamp}_{random_id}.json"
        filepath = os.path.join(UPLOADS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4)
    except Exception:
        return build_response(500, "Internal Server Error", body=b"<h1>500 Internal Server Error</h1>")

    response_body = {
        "status": "success",
        "message": "File created successfully",
        "filepath": os.path.join('/uploads', filename)
    }
    response_body_json = json.dumps(response_body).encode('utf-8')
    response_headers['Content-Type'] = 'application/json'
    response_headers['Content-Length'] = str(len(response_body_json))
    
    return build_response(201, "Created", response_headers, response_body_json)

# --- Thread Pool ---
class ThreadPool:
    def __init__(self, num_threads):
        self.tasks = queue.Queue()
        for i in range(num_threads):
            thread = threading.Thread(target=self.worker, args=(i+1,), daemon=True)
            thread.start()

    def worker(self, thread_id):
        while True:
            client_socket, address, server_host, server_port = self.tasks.get()
            handle_client_connection(client_socket, address, server_host, server_port)
            self.tasks.task_done()

    def add_task(self, task):
        self.tasks.put(task)

# --- Final Connection Handler ---
def handle_client_connection(client_socket, address, server_host, server_port):
    request_count = 0
    MAX_REQUESTS = 100
    TIMEOUT = 30
    
    client_socket.settimeout(TIMEOUT)

    try:
        while request_count < MAX_REQUESTS:
            socket_file = client_socket.makefile('rb', 0)
            
            request_line_bytes = socket_file.readline()
            if not request_line_bytes:
                break
            
            request_line = request_line_bytes.decode('utf-8').strip()
            if not request_line:
                continue

            method, path, http_version = request_line.split()
            
            headers = {}
            while True:
                line = socket_file.readline().decode('utf-8').strip()
                if not line: break
                key, value = line.split(': ', 1)
                headers[key.lower()] = value
            
            # Host Header Validation
            host_header = headers.get('host')
            server_address = f"{server_host}:{server_port}"

            if http_version == "HTTP/1.1" and not host_header:
                response = build_response(400, "Bad Request", body=b"<h1>400 Bad Request: Missing Host header</h1>")
                client_socket.sendall(response)
                break
            
            if host_header and host_header != server_address and host_header != server_host:
                response = build_response(403, "Forbidden", body=b"<h1>403 Forbidden: Host header mismatch</h1>")
                client_socket.sendall(response)
                break

            print(f"Request #{request_count + 1} from {address}: {method} {path}")

            body_data = b''
            if method == 'POST':
                content_length = int(headers.get('content-length', 0))
                if content_length > 0:
                    body_data = socket_file.read(content_length)

            keep_alive = True
            if headers.get('connection', 'keep-alive').lower() == 'close':
                keep_alive = False
            
            response_headers = {}
            if keep_alive and request_count < MAX_REQUESTS - 1:
                response_headers['Connection'] = 'keep-alive'
                response_headers['Keep-Alive'] = f'timeout={TIMEOUT}, max={MAX_REQUESTS - request_count - 1}'
            else:
                response_headers['Connection'] = 'close'
                keep_alive = False

            if method == 'GET':
                response = handle_get_request(path, response_headers)
            elif method == 'POST':
                response = handle_post_request(headers, body_data, response_headers)
            else:
                response = build_response(405, "Method Not Allowed", response_headers, b"<h1>405 Method Not Allowed</h1>")

            client_socket.sendall(response)
            request_count += 1
            
            if not keep_alive:
                break

    except socket.timeout:
        print(f"Connection from {address} timed out after {TIMEOUT}s of inactivity.")
    except Exception as e:
        print(f"!!! SERVER LOG: An error occurred: {e}")
    finally:
        client_socket.close()
        print(f"Connection with {address} closed. Total requests: {request_count}")

# --- Main Server Function ---
def main():
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    HOST = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
    POOL_SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    thread_pool = ThreadPool(POOL_SIZE)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(50)
    
    print(f"[SERVER] Started on http://{HOST}:{PORT}")
    print(f"[SERVER] Thread pool size: {POOL_SIZE}")

    try:
        while True:
            client_socket, address = server_socket.accept()
            task_data = (client_socket, address, HOST, PORT)
            thread_pool.add_task(task_data)
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()