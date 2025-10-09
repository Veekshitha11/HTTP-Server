import threading
import queue
import time
import datetime


class ThreadPool:
    """
    A fixed-size thread pool for handling concurrent HTTP client connections.

    - Maintains a queue of tasks (client sockets)
    - Uses worker threads to execute tasks concurrently
    - Waits when the pool is full and resumes when a worker is free
    - Logs all thread pool events
    """

    def __init__(self, max_threads=10):
        self.max_threads = max_threads
        self.task_queue = queue.Queue()
        self.threads = []
        self.active_threads = 0
        self.lock = threading.Lock()
        self.shutdown_flag = threading.Event()

        # Start worker threads
        for i in range(max_threads):
            worker = threading.Thread(target=self.worker_loop, name=f"Thread-{i+1}", daemon=True)
            worker.start()
            self.threads.append(worker)

        self.log(f"Thread pool initialized with {max_threads} threads")

    # ----------------------------------------------------------------

    def log(self, message):
        """Timestamped console log for thread pool activity"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    # ----------------------------------------------------------------

    def worker_loop(self):
        """
        Continuously fetch tasks from the queue and execute them.
        Each task is a function + its arguments.
        """
        while not self.shutdown_flag.is_set():
            try:
                func, args = self.task_queue.get(timeout=1)
                with self.lock:
                    self.active_threads += 1

                thread_name = threading.current_thread().name
                self.log(f"[{thread_name}] Picked up new task")

                try:
                    func(*args)
                except Exception as e:
                    self.log(f"[{thread_name}] ERROR: {e}")

                with self.lock:
                    self.active_threads -= 1

                self.task_queue.task_done()
                self.log(f"[{thread_name}] Finished task")

            except queue.Empty:
                continue

    # ----------------------------------------------------------------

    def submit(self, func, *args):
        """
        Add a new task to the queue.
        If the queue is full, connection is queued (simulating waiting clients).
        """
        try:
            if self.task_queue.qsize() >= 50:
                self.log("⚠️  Queue is saturated (50 waiting connections)")
                raise queue.Full

            self.task_queue.put((func, args))
            self.log(f"Task queued (pending tasks: {self.task_queue.qsize()})")

        except queue.Full:
            self.log("⚠️  Connection rejected: Service Unavailable (503)")

    # ----------------------------------------------------------------

    def get_status(self):
        """Return current thread pool status."""
        with self.lock:
            return {
                "active": self.active_threads,
                "available": self.max_threads - self.active_threads,
                "queued": self.task_queue.qsize(),
            }

    # ----------------------------------------------------------------

    def shutdown(self):
        """Gracefully shut down all worker threads."""
        self.log("Shutting down thread pool...")
        self.shutdown_flag.set()

        for t in self.threads:
            t.join(timeout=1)
        self.log("All threads have been stopped")
