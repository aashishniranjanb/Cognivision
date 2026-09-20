"""Spatial Virtual Line & Boundary Crossing Detector with directional vector analysis."""
from typing import Tuple, Optional, Dict
import time

class VirtualLine:
    def __init__(
        self,
        pt1: Tuple[int, int],
        pt2: Tuple[int, int],
        name: str = "ENTRY_LINE",
        expected_in_direction: str = "TOP_TO_BOTTOM"  # or "LEFT_TO_RIGHT"
    ):
        self.pt1 = pt1
        self.pt2 = pt2
        self.name = name
        self.expected_in_direction = expected_in_direction

    def point_side(self, pt: Tuple[int, int]) -> float:
        """Determines which side of the oriented line (pt1 -> pt2) a point lies on via cross product."""
        x1, y1 = self.pt1
        x2, y2 = self.pt2
        px, py = pt
        # Cross product: (x2 - x1)*(py - y1) - (y2 - y1)*(px - x1)
        return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)

class LineCrossingDetector:
    def __init__(self, virtual_line: VirtualLine, cooldown_seconds: float = 3.0):
        self.line = virtual_line
        self.cooldown_seconds = cooldown_seconds
        
        # track_id -> (last_side, last_timestamp, last_emitted_time)
        self.track_states: Dict[int, dict] = {}

    def check_crossing(self, track_id: int, current_centroid: Tuple[int, int]) -> Optional[str]:
        """Checks if a track has crossed the virtual line. Returns 'IN', 'OUT', or None."""
        now = time.time()
        current_side = self.line.point_side(current_centroid)

        if track_id not in self.track_states:
            self.track_states[track_id] = {
                "side": current_side,
                "last_time": now,
                "last_event_time": 0.0,
                "emitted": False
            }
            return None

        state = self.track_states[track_id]
        prev_side = state["side"]
        last_event_time = state["last_event_time"]

        direction = None
        # Strict sign change indicates crossing the line segment boundary
        if prev_side * current_side < 0:
            # Check cooldown to prevent duplicate triggers while hovering on line
            if (now - last_event_time) > self.cooldown_seconds:
                if prev_side < 0 and current_side > 0:
                    direction = "IN"
                else:
                    direction = "OUT"
                
                state["last_event_time"] = now
                state["emitted"] = True

        state["side"] = current_side
        state["last_time"] = now
        return direction

    def cleanup_inactive_tracks(self, active_track_ids: set):
        to_del = [tid for tid in self.track_states if tid not in active_track_ids]
        for tid in to_del:
            del self.track_states[tid]
