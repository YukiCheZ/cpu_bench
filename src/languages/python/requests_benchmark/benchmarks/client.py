import requests
import time
from benchmarks.local_file_adapter import LocalFileAdapter

class RequestsWorkloads:
    def __init__(self, filepath):
        self.file_url = f"file://{filepath}"
        self.session = requests.Session()
        self.session.mount("file://", LocalFileAdapter())

    def warmup(self, count):
        for _ in range(count):
            resp = self.session.get(self.file_url)
            _ = resp.json()

    def run(self, iterations=1, warmup_count=3):
        # warmup
        self.warmup(warmup_count)

        start = time.perf_counter()
        for _ in range(iterations):
            resp = self.session.get(self.file_url)
            _ = resp.json()
        elapsed = time.perf_counter() - start

        return elapsed
