"""Decoupled thread-safe FrameBuffer with bounded queue and drop-oldest policy."""
from queue import Queue
from dataclasses import dataclass
from typing import Optional, Any
import numpy as np


@dataclass
class BufferedFrame:
    frame_id: int
    timestamp: float
    frame: np.ndarray
    source_name: str


class FrameBuffer:
    def __init__(self, max_size: int = 30):
        self.max_size = max_size
        self.queue: Queue[BufferedFrame] = Queue(maxsize=max_size)
        self.dropped_frames: int = 0
        self.total_received: int = 0
        self.total_consumed: int = 0

    def put(self, frame_item: BufferedFrame) -> bool:
        """Pushes frame into buffer. Drops oldest if full to preserve live stream immediacy."""
        dropped = False
        if self.queue.full():
            try:
                self.queue.get_nowait()
                self.dropped_frames += 1
                dropped = True
            except Exception:
                pass

        self.queue.put(frame_item)
        self.total_received += 1
        return dropped

    def get(self, timeout: Optional[float] = 1.0) -> Optional[BufferedFrame]:
        """Pops oldest frame. Returns None if timed out."""
        try:
            item = self.queue.get(timeout=timeout)
            self.total_consumed += 1
            return item
        except Exception:
            return None

    def size(self) -> int:
        return self.queue.qsize()

    def is_full(self) -> bool:
        return self.queue.full()

    def stats(self) -> dict:
        return {
            "size": self.size(),
            "max_size": self.max_size,
            "dropped": self.dropped_frames,
            "received": self.total_received,
            "consumed": self.total_consumed,
        }
