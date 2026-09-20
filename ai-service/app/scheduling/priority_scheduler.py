# Priority scheduler
import time
from enum import IntEnum
from dataclasses import dataclass, field
import heapq
from typing import Optional, Any

class PriorityTier(IntEnum):
    CRITICAL_BOUNDARY = 1
    NEW_TRACK = 2
    TENTATIVE_REFRESH = 3
    CONFIRMED_TTL = 4

@dataclass(order=True)
class RecognitionTask:
    priority: int
    created_at: float = field(compare=True)
    task_id: str = field(compare=False)
    track_id: int = field(compare=False)
    camera_id: str = field(compare=False)
    crop_data: Any = field(compare=False)
    metadata: dict = field(default_factory=dict, compare=False)

class PriorityInferenceScheduler:
    def __init__(self, max_queue_size: int = 100):
        self.max_queue_size = max_queue_size
        self._queue = []
        self._task_count = 0
        self.total_scheduled = 0
        self.total_executed = 0
        self.total_dropped = 0

    def schedule(self, track_id: int, camera_id: str, crop_data: Any, tier: PriorityTier = PriorityTier.NEW_TRACK, metadata: Optional[dict] = None) -> bool:
        if len(self._queue) >= self.max_queue_size:
            lowest = self._queue[-1]
            if lowest.priority > int(tier):
                self._queue.pop()
                self.total_dropped += 1
            else:
                self.total_dropped += 1
                return False

        self._task_count += 1
        now = time.perf_counter()
        task = RecognitionTask(
            priority=int(tier),
            created_at=now,
            task_id=chr(84)+chr(65)+chr(83)+chr(75)+'_' + camera_id + '_' + str(track_id) + '_' + str(self._task_count),
            track_id=track_id,
            camera_id=camera_id,
            crop_data=crop_data,
            metadata=metadata or {}
        )
        heapq.heappush(self._queue, task)
        self.total_scheduled += 1
        return True

    def get_next_task(self) -> Optional[RecognitionTask]:
        if not self._queue:
            return None
        task = heapq.heappop(self._queue)
        self.total_executed += 1
        return task

    def pending_count(self) -> int:
        return len(self._queue)

    def clear(self):
        self._queue.clear()
