"""Thread-safe ring buffer with drop-oldest policy and latency tracking."""
import time
import threading
from collections import deque
from dataclasses import dataclass
from typing import Optional, Any
import numpy as np

@dataclass
class FramePacket:
    frame_id: int
    camera_id: str
    timestamp: float          # Time captured (seconds)
    frame: np.ndarray         # Image array (BGR)
    metadata: Optional[dict] = None

class FrameBuffer:
    def __init__(self, maxsize: int = 30):
        self.maxsize = maxsize
        self._deque: deque[FramePacket] = deque(maxlen=maxsize)
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        
        # Diagnostics
        self.total_pushed: int = 0
        self.total_dropped: int = 0
        self.total_popped: int = 0

    def push(self, packet: FramePacket) -> bool:
        """Pushes a frame packet. If buffer is full, drops the oldest frame (real-time liveness)."""
        with self._lock:
            dropped = False
            if len(self._deque) >= self.maxsize:
                self._deque.popleft()
                self.total_dropped += 1
                dropped = True
            
            self._deque.append(packet)
            self.total_pushed += 1
            self._not_empty.notify()
            return dropped

    def pop(self, timeout: Optional[float] = 1.0) -> Optional[FramePacket]:
        """Pops the oldest available frame. Blocks up to `timeout` seconds if empty."""
        with self._lock:
            start_time = time.time()
            while len(self._deque) == 0:
                remaining = None
                if timeout is not None:
                    remaining = timeout - (time.time() - start_time)
                    if remaining <= 0:
                        return None
                if not self._not_empty.wait(timeout=remaining):
                    return None
                
            packet = self._deque.popleft()
            self.total_popped += 1
            return packet

    def peek_latest(self) -> Optional[FramePacket]:
        """Returns the most recent frame without removing it."""
        with self._lock:
            if not self._deque:
                return None
            return self._deque[-1]

    def clear(self):
        with self._lock:
            self._deque.clear()

    @property
    def qsize(self) -> int:
        with self._lock:
            return len(self._deque)

    def stats(self) -> dict:
        with self._lock:
            return {
                "size": len(self._deque),
                "maxsize": self.maxsize,
                "pushed": self.total_pushed,
                "dropped": self.total_dropped,
                "popped": self.total_popped,
            }
