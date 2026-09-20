"""Cross-Camera Event Reconciler detecting and resolving simultaneous contradictory events."""
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
import time
from app.attendance.event import AttendanceEvent

@dataclass
class ConflictResolution:
    is_conflict: bool
    action: str              # "ACCEPTED", "DROPPED_CONTRADICTORY", "RAPID_FLAP_SUPPRESSED"
    reason: str

class EventReconciler:
    def __init__(self, min_event_interval_sec: float = 2.0):
        self.min_interval = min_event_interval_sec
        # student_id -> latest AttendanceEvent
        self.last_student_events: Dict[str, AttendanceEvent] = {}

    def reconcile(self, new_event: Any) -> ConflictResolution:
        sid = getattr(new_event, "student_id", None)
        now = getattr(new_event, "timestamp", time.time())
        new_direction = getattr(new_event, "direction", getattr(new_event, "event_type", None))
        new_loc = getattr(new_event, "location_id", getattr(new_event, "classroom_id", "UNKNOWN"))

        if not sid:
            return ConflictResolution(False, "ACCEPTED", "Non-student event")

        if sid not in self.last_student_events:
            self.last_student_events[sid] = new_event
            return ConflictResolution(False, "ACCEPTED", "First event for student")

        last_evt = self.last_student_events[sid]
        last_direction = getattr(last_evt, "direction", getattr(last_evt, "event_type", None))
        last_loc = getattr(last_evt, "location_id", getattr(last_evt, "classroom_id", "UNKNOWN"))
        delta = now - getattr(last_evt, "timestamp", now)

        # Conflict Rule 1: Contradictory events (IN then OUT or vice versa) in < 2 seconds
        if delta < self.min_interval and last_direction != new_direction and last_loc == new_loc:
            return ConflictResolution(
                is_conflict=True,
                action="DROPPED_CONTRADICTORY",
                reason=f"Contradictory {last_direction}->{new_direction} in {delta:.2f}s on {new_loc}"
            )

        # Conflict Rule 2: Teleportation check (different classrooms within 5 seconds)
        if delta < 5.0 and last_loc != new_loc and last_loc != "OUTSIDE":
            return ConflictResolution(
                is_conflict=True,
                action="RAPID_FLAP_SUPPRESSED",
                reason=f"Impossible location jump: {last_loc} to {new_loc} in {delta:.2f}s"
            )

        self.last_student_events[sid] = new_event
        return ConflictResolution(False, "ACCEPTED", "Valid sequential event")
