import threading
import requests
import time

# Server URL
BASE_URL = "http://localhost:8080"

# List of files to test
FILES = ["/", "/about.html", "/contact.html", "/sample.txt", "/logo.png", "/photo.jpg"]

# Function to perform GET request
def get_file(path):
    try:
        start = time.time()
        r = requests.get(BASE_URL + path)
        elapsed = time.time() - start
        print(f"[{threading.current_thread().name}] GET {path} -> {r.status_code} ({elapsed:.2f}s)")
    except Exception as e:
        print(f"[{threading.current_thread().name}] Error fetching {path}: {e}")

# Number of concurrent threads
NUM_THREADS = 10

threads = []

# Start multiple threads
for i in range(NUM_THREADS):
    file_to_fetch = FILES[i % len(FILES)]
    t = threading.Thread(target=get_file, args=(file_to_fetch,), name=f"Thread-{i+1}")
    t.start()
    threads.append(t)

# Wait for all threads to complete
for t in threads:
    t.join()

print("✅ All concurrent GET requests completed.")
