"""Comprehensive Attendance Engine: Coordinates Line Crossing, Event Deduplication, Duration, and Audit Logging."""
import time
import uuid
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from app.attendance.event import AttendanceEvent
from app.attendance.zone import LineCrossingDetector, VirtualLine
from app.attendance.state import AttendanceStateMachine, AttendanceStatus
from app.attendance.duration import DurationEngine, PresenceSession

class AttendanceEngine:
    def __init__(
        self,
        camera_id: str = "ENTRY_CAM_01",
        location_id: str = "CLASSROOM_203",
        log_file: str = "data/attendance_records/events.jsonl",
        virtual_line: Optional[VirtualLine] = None
    ):
        self.camera_id = camera_id
        self.location_id = location_id
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Default horizontal line across middle of standard 720p/540p frame
        if virtual_line is None:
            virtual_line = VirtualLine(pt1=(50, 360), pt2=(1230, 360), name="CLASSROOM_DOOR")

        self.crossing_detector = LineCrossingDetector(virtual_line, cooldown_seconds=4.0)
        self.state_machine = AttendanceStateMachine()
        self.duration_engine = DurationEngine()
        
        # In-memory recent events for UI HUD
        self.recent_events: List[AttendanceEvent] = []

    def process_observation(
        self,
        track_id: int,
        student_id: Optional[str],
        centroid: Tuple[int, int],
        confidence: float,
        is_confirmed: bool
    ) -> Optional[AttendanceEvent]:
        """Checks spatial crossing and emits deduplicated attendance event if identity is confirmed."""
        direction = self.crossing_detector.check_crossing(track_id, centroid)
        if direction is None:
            return None

        # Only confirmed students generate valid audited attendance events (Requirement #10 & #11)
        if not is_confirmed or student_id is None:
            print(f"[AttendanceEngine] Line crossed by Track {track_id} ({direction}), but identity is not confirmed. Event withheld.")
            return None

        now = time.time()
        iso_str = datetime.fromtimestamp(now).strftime("%Y-%m-%dT%H:%M:%S")
        event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"

        event = AttendanceEvent(
            event_id=event_id,
            student_id=student_id,
            camera_id=self.camera_id,
            location_id=self.location_id,
            direction=direction,
            timestamp=now,
            timestamp_iso=iso_str,
            track_id=track_id,
            confidence=confidence
        )

        # Update State Machine & Duration
        self.state_machine.transition_on_event(
            student_id=student_id,
            direction=direction,
            location_id=self.location_id,
            timestamp=now
        )

        if direction == "IN":
            self.duration_engine.record_entry(student_id, self.location_id, now)
        elif direction == "OUT":
            self.duration_engine.record_exit(student_id, now)

        # Append to audit log
        self._audit_log(event)
        self.recent_events.append(event)
        if len(self.recent_events) > 10:
            self.recent_events.pop(0)

        return event

    def _audit_log(self, event: AttendanceEvent):
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            print(f"[AttendanceEngine] Failed to write audit event: {e}")

    def get_summary(self) -> dict:
        inside_students = [
            sid for sid, s in self.state_machine.states.items()
            if s.current_status == AttendanceStatus.INSIDE
        ]
        return {
            "total_events": len(self.recent_events),
            "inside_count": len(inside_students),
            "inside_students": inside_students,
            "active_sessions": {
                sid: sess.current_duration_formatted
                for sid, sess in self.duration_engine.active_sessions.items()
            }
        }
