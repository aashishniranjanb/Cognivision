"""Cross-Camera Event Reconciler detecting and resolving simultaneous contradictory events."""
from dataclasses import dataclass
from typing import Optional, Dict, List
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

    def reconcile(self, new_event: AttendanceEvent) -> ConflictResolution:
        sid = new_event.student_id
        now = new_event.timestamp

        if sid not in self.last_student_events:
            self.last_student_events[sid] = new_event
            return ConflictResolution(False, "ACCEPTED", "First event for student")

        last_evt = self.last_student_events[sid]
        delta = now - last_evt.timestamp

        # Conflict Rule 1: Contradictory events (IN then OUT or vice versa) in < 2 seconds
        if delta < self.min_interval and last_evt.direction != new_event.direction and last_evt.location_id == new_event.location_id:
            return ConflictResolution(
                is_conflict=True,
                action="DROPPED_CONTRADICTORY",
                reason=f"Contradictory {last_evt.direction}->{new_event.direction} in {delta:.2f}s on {new_event.location_id}"
            )

        # Conflict Rule 2: Teleportation check (different classrooms within 5 seconds)
        if delta < 5.0 and last_evt.location_id != new_event.location_id and last_evt.location_id != "OUTSIDE":
            return ConflictResolution(
                is_conflict=True,
                action="RAPID_FLAP_SUPPRESSED",
                reason=f"Impossible location jump: {last_evt.location_id} to {new_event.location_id} in {delta:.2f}s"
            )

        self.last_student_events[sid] = new_event
        return ConflictResolution(False, "ACCEPTED", "Valid sequential event")
