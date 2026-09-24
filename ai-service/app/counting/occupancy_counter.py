"""Occupancy Counter: Computes vision-based real-time headcount vs event-derived cumulative occupancy."""
from typing import Dict, Optional, List
import time

class OccupancyCounter:
    def __init__(self, classroom_id: str, baseline_occupancy: int = 0):
        self.classroom_id = classroom_id
        self.baseline_occupancy = baseline_occupancy
        
        self.in_event_count: int = 0
        self.out_event_count: int = 0
        self.last_vision_count: int = 0
        self.last_updated: float = time.time()

    def update_vision_count(self, count: int, timestamp: Optional[float] = None):
        """Updates instantaneous headcount detected physically by camera vision."""
        self.last_vision_count = max(0, count)
        self.last_updated = timestamp if timestamp is not None else time.time()

    def record_event(self, direction: str, count: int = 1):
        """Records confirmed physical door entry or exit crossing events."""
        if direction.upper() == "IN":
            self.in_event_count += count
        elif direction.upper() == "OUT":
            self.out_event_count += count
        self.last_updated = time.time()

    @property
    def event_occupancy(self) -> int:
        """Net occupancy derived from crossing events: baseline + IN - OUT."""
        return max(0, self.baseline_occupancy + self.in_event_count - self.out_event_count)

    @property
    def vision_count(self) -> int:
        """Current physical people observed in-frame by vision sensors."""
        return self.last_vision_count

    def get_occupancy_snapshot(self) -> dict:
        return {
            "classroom_id": self.classroom_id,
            "vision_count": self.vision_count,
            "event_occupancy": self.event_occupancy,
            "in_events": self.in_event_count,
            "out_events": self.out_event_count,
            "difference": abs(self.vision_count - self.event_occupancy),
            "timestamp": self.last_updated
        }
