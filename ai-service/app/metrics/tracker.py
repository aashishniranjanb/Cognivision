"""Metrics tracker for real-time video stream telemetry (FPS, Latency, Queue Depth)."""
import time
from collections import deque

class StreamMetrics:
    def __init__(self, window_sec: float = 3.0):
        self.window_sec = window_sec
        self._input_timestamps: deque[float] = deque()
        self._proc_timestamps: deque[float] = deque()
        self._latencies_ms: deque[float] = deque(maxlen=60)
        self.last_frame_time: float = 0.0

    def record_input_frame(self):
        now = time.time()
        self._input_timestamps.append(now)
        self.last_frame_time = now
        self._prune(self._input_timestamps, now)

    def record_processed_frame(self, latency_ms: float):
        now = time.time()
        self._proc_timestamps.append(now)
        self._latencies_ms.append(latency_ms)
        self._prune(self._proc_timestamps, now)

    def _prune(self, dq: deque, now: float):
        cutoff = now - self.window_sec
        while dq and dq[0] < cutoff:
            dq.popleft()

    @property
    def input_fps(self) -> float:
        now = time.time()
        self._prune(self._input_timestamps, now)
        if len(self._input_timestamps) < 2:
            return 0.0
        duration = self._input_timestamps[-1] - self._input_timestamps[0]
        return (len(self._input_timestamps) - 1) / duration if duration > 0 else 0.0

    @property
    def processing_fps(self) -> float:
        now = time.time()
        self._prune(self._proc_timestamps, now)
        if len(self._proc_timestamps) < 2:
            return 0.0
        duration = self._proc_timestamps[-1] - self._proc_timestamps[0]
        return (len(self._proc_timestamps) - 1) / duration if duration > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        if not self._latencies_ms:
            return 0.0
        return sum(self._latencies_ms) / len(self._latencies_ms)
