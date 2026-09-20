"""Multi-Camera Global Coordinator: Reconciles concurrent streams, camera-specific Track IDs, and global student state."""
from dataclasses import dataclass
from typing import Dict, List, Optional
import time
from app.attendance.event import AttendanceEvent

@dataclass
class GlobalStudentState:
    student_id: str
    current_location: str
    status: str             # "INSIDE", "EXITED"
    last_camera: str
    last_event_time: float
    total_time_inside: float = 0.0

class MultiCameraCoordinator:
    def __init__(self):
        # student_id -> GlobalStudentState
        self.global_students: Dict[str, GlobalStudentState] = {}
        # Immutable global event log
        self.global_events: List[AttendanceEvent] = []

    def handle_event(self, event: AttendanceEvent) -> GlobalStudentState:
        """
        Reconciles events from different cameras:
          ENTRY_CAM_01 / Track 17 -> STU001 (IN)
          EXIT_CAM_01  / Track 04 -> STU001 (OUT)
        """
        sid = event.student_id
        now = event.timestamp

        if sid not in self.global_students:
            self.global_students[sid] = GlobalStudentState(
                student_id=sid,
                current_location=event.location_id,
                status="INSIDE" if event.direction == "IN" else "EXITED",
                last_camera=event.camera_id,
                last_event_time=now
            )
        else:
            state = self.global_students[sid]
            if event.direction == "IN":
                state.status = "INSIDE"
                state.current_location = event.location_id
                state.last_camera = event.camera_id
                state.last_event_time = now
            elif event.direction == "OUT":
                if state.status == "INSIDE":
                    state.total_time_inside += max(0.0, now - state.last_event_time)
                state.status = "EXITED"
                state.last_camera = event.camera_id
                state.last_event_time = now

        self.global_events.append(event)
        return self.global_students[sid]

    def get_summary(self) -> dict:
        inside = [sid for sid, s in self.global_students.items() if s.status == "INSIDE"]
        exited = [sid for sid, s in self.global_students.items() if s.status == "EXITED"]
        return {
            "total_students_tracked": len(self.global_students),
            "inside_count": len(inside),
            "inside_students": inside,
            "exited_count": len(exited),
            "total_events": len(self.global_events)
        }
