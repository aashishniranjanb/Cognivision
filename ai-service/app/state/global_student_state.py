"""Global Student State: Single Source of Truth for Student Presence across all 5 Classrooms."""
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
import time
import json

@dataclass
class GlobalStudentState:
    student_id: str
    current_location: str          # "OUTSIDE" or e.g. "CLASSROOM_203"
    state: str                     # "INSIDE", "OUTSIDE", "TRANSIT"
    entry_time: Optional[float]    # Timestamp when entering current room
    last_seen: float               # Latest biometric observation
    last_camera: str               # e.g. "ENTRY_203"
    accumulated_inside_sec: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

class GlobalStudentStateManager:
    def __init__(self):
        # student_id -> GlobalStudentState
        self.students: Dict[str, GlobalStudentState] = {}

    def get_or_create(self, student_id: str) -> GlobalStudentState:
        if student_id not in self.students:
            self.students[student_id] = GlobalStudentState(
                student_id=student_id,
                current_location="OUTSIDE",
                state="OUTSIDE",
                entry_time=None,
                last_seen=time.time(),
                last_camera="UNKNOWN",
                accumulated_inside_sec=0.0
            )
        return self.students[student_id]

    def update_presence(self, student_id: str, location_id: str, direction: str, camera_id: str, timestamp: float) -> GlobalStudentState:
        s = self.get_or_create(student_id)
        s.last_seen = timestamp
        s.last_camera = camera_id

        if direction == "IN":
            s.state = "INSIDE"
            s.current_location = location_id
            s.entry_time = timestamp
        elif direction == "OUT":
            if s.state == "INSIDE" and s.entry_time is not None:
                s.accumulated_inside_sec += max(0.0, timestamp - s.entry_time)
            s.state = "OUTSIDE"
            s.current_location = "OUTSIDE"
            s.entry_time = None

        return s

    def get_classroom_occupants(self, classroom_id: str) -> List[str]:
        return [
            sid for sid, s in self.students.items()
            if s.state == "INSIDE" and s.current_location == classroom_id
        ]

    def get_campus_summary(self) -> dict:
        total = len(self.students)
        inside = sum(1 for s in self.students.values() if s.state == "INSIDE")
        outside = total - inside
        return {
            "total_enrolled": total,
            "present_campus": inside,
            "outside_campus": outside
        }

    def get_all_states(self) -> Dict[str, GlobalStudentState]:
        return dict(self.students)
