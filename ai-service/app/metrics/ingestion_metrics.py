"""High-precision metrics collector for stream ingestion."""
import time
from collections import deque


class IngestionMetrics:
    def __init__(self, window_sec: float = 3.0):
        self.window_sec = window_sec
        self._input_times: deque[float] = deque()
        self._proc_times: deque[float] = deque()
        self._latencies_ms: deque[float] = deque(maxlen=60)

    def record_input(self):
        now = time.perf_counter()
        self._input_times.append(now)
        self._prune(self._input_times, now)

    def record_processed(self, latency_ms: float):
        now = time.perf_counter()
        self._proc_times.append(now)
        self._latencies_ms.append(latency_ms)
        self._prune(self._proc_times, now)

    def _prune(self, dq: deque, now: float):
        cutoff = now - self.window_sec
        while dq and dq[0] < cutoff:
            dq.popleft()

    @property
    def input_fps(self) -> float:
        now = time.perf_counter()
        self._prune(self._input_times, now)
        if len(self._input_times) < 2:
            return 0.0
        duration = self._input_times[-1] - self._input_times[0]
        return (len(self._input_times) - 1) / duration if duration > 0 else 0.0

    @property
    def process_fps(self) -> float:
        now = time.perf_counter()
        self._prune(self._proc_times, now)
        if len(self._proc_times) < 2:
            return 0.0
        duration = self._proc_times[-1] - self._proc_times[0]
        return (len(self._proc_times) - 1) / duration if duration > 0 else 0.0

    @property
    def latency_ms(self) -> float:
        if not self._latencies_ms:
            return 0.0
        return sum(self._latencies_ms) / len(self._latencies_ms)
