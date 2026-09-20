"""Exponential Backoff and Reconnect Policy for CCTV/RTSP Network Drops."""
import time
from typing import Optional

class ReconnectPolicy:
    def __init__(
        self,
        base_delay_sec: float = 1.0,
        max_delay_sec: float = 30.0,
        backoff_factor: float = 2.0,
        max_attempts: int = 15
    ):
        self.base_delay = base_delay_sec
        self.max_delay = max_delay_sec
        self.backoff_factor = backoff_factor
        self.max_attempts = max_attempts
        self.attempts = 0
        self.last_attempt_time = 0.0

    def can_reconnect(self) -> bool:
        if self.attempts >= self.max_attempts:
            return False
        if self.attempts == 0:
            return True
        delay = min(self.max_delay, self.base_delay * (self.backoff_factor ** max(0, self.attempts - 1)))
        return (time.time() - self.last_attempt_time) >= delay

    def record_attempt(self):
        self.attempts += 1
        self.last_attempt_time = time.time()

    def reset(self):
        self.attempts = 0
        self.last_attempt_time = 0.0

