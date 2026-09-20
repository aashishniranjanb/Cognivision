"""Attendance State Machine tracking per-student presence status and period compliance."""
from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

class AttendanceStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    TENTATIVE = "TENTATIVE"
    CONFIRMED = "CONFIRMED"
    INSIDE = "INSIDE"
    EXITED = "EXITED"
    UNCERTAIN = "UNCERTAIN"

@dataclass
class StudentPresenceState:
    student_id: str
    current_status: AttendanceStatus
    current_location: Optional[str] = None
    last_event_direction: Optional[str] = None
    last_event_time: Optional[float] = None
    total_inside_duration: float = 0.0

class AttendanceStateMachine:
    def __init__(self):
        # student_id -> StudentPresenceState
        self.states: Dict[str, StudentPresenceState] = {}

    def get_or_create(self, student_id: str) -> StudentPresenceState:
        if student_id not in self.states:
            self.states[student_id] = StudentPresenceState(
                student_id=student_id,
                current_status=AttendanceStatus.UNKNOWN
            )
        return self.states[student_id]

    def transition_on_event(self, student_id: str, direction: str, location_id: str, timestamp: float) -> StudentPresenceState:
        state = self.get_or_create(student_id)
        
        if direction == "IN":
            state.current_status = AttendanceStatus.INSIDE
            state.current_location = location_id
            state.last_event_direction = "IN"
            state.last_event_time = timestamp
        elif direction == "OUT":
            state.current_status = AttendanceStatus.EXITED
            state.last_event_direction = "OUT"
            state.last_event_time = timestamp

        return state
