"""Transition Validator: Verifies student spatio-temporal transitions across classrooms,
detects impossible location jumps (teleportation), and suppresses duplicate flap events.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import time

@dataclass
class TransitionResult:
    is_valid: bool
    action: str              # "ACCEPTED", "SUPPRESSED_DUPLICATE", "LOCATION_TRANSITION_ANOMALY", "AUTO_RECONCILED"
    current_state: str       # "INSIDE", "OUTSIDE"
    current_location: str    # "CLASSROOM_101", "OUTSIDE", etc.
    reason: str

@dataclass
class StudentPresenceState:
    student_id: str
    state: str = "OUTSIDE"            # "INSIDE" or "OUTSIDE"
    location_id: str = "OUTSIDE"
    last_event_time: float = 0.0
    last_direction: Optional[str] = None

class TransitionValidator:
    def __init__(self, min_transit_seconds: float = 4.0, flap_window_seconds: float = 2.0):
        self.min_transit_seconds = min_transit_seconds
        self.flap_window_seconds = flap_window_seconds
        # student_id -> StudentPresenceState
        self.students: Dict[str, StudentPresenceState] = {}

    def get_or_create(self, student_id: str) -> StudentPresenceState:
        if student_id not in self.students:
            self.students[student_id] = StudentPresenceState(student_id=student_id)
        return self.students[student_id]

    def validate_transition(
        self,
        student_id: str,
        direction: str,
        target_location: str,
        timestamp: Optional[float] = None
    ) -> TransitionResult:
        """Validates incoming movement event against physical laws of movement."""
        now = timestamp if timestamp is not None else time.time()
        st = self.get_or_create(student_id)
        delta_t = now - st.last_event_time if st.last_event_time > 0 else 9999.0

        dir_norm = direction.upper()

        # 1. Rapid Flap Detection (< flap_window_seconds)
        if delta_t < self.flap_window_seconds and st.last_direction != dir_norm and st.location_id == target_location:
            return TransitionResult(
                is_valid=False,
                action="SUPPRESSED_DUPLICATE",
                current_state=st.state,
                current_location=st.location_id,
                reason=f"Rapid directional flap ({st.last_direction}->{dir_norm}) in {delta_t:.2f}s suppressed"
            )

        # 2. Impossible Location Jump (Teleportation across different classrooms)
        if (
            st.state == "INSIDE"
            and st.location_id != target_location
            and target_location != "OUTSIDE"
            and delta_t < self.min_transit_seconds
        ):
            return TransitionResult(
                is_valid=False,
                action="LOCATION_TRANSITION_ANOMALY",
                current_state=st.state,
                current_location=st.location_id,
                reason=f"Impossible location jump: {st.location_id} to {target_location} in {delta_t:.2f}s (Min required: {self.min_transit_seconds}s)"
            )

        # 3. Duplicate Inward / Outward Events
        if dir_norm == "IN" and st.state == "INSIDE" and st.location_id == target_location:
            # Student already inside this room
            return TransitionResult(
                is_valid=False,
                action="SUPPRESSED_DUPLICATE",
                current_state=st.state,
                current_location=st.location_id,
                reason=f"Student {student_id} already marked INSIDE {target_location}"
            )

        if dir_norm == "OUT" and st.state == "OUTSIDE":
            # Student already outside
            return TransitionResult(
                is_valid=False,
                action="SUPPRESSED_DUPLICATE",
                current_state=st.state,
                current_location=st.location_id,
                reason=f"Student {student_id} already marked OUTSIDE campus"
            )

        # 4. Auto-reconciled room switch: Inside Room A -> Enters Room B after valid transit time
        if dir_norm == "IN" and st.state == "INSIDE" and st.location_id != target_location:
            prev_room = st.location_id
            st.location_id = target_location
            st.state = "INSIDE"
            st.last_event_time = now
            st.last_direction = "IN"
            return TransitionResult(
                is_valid=True,
                action="AUTO_RECONCILED",
                current_state="INSIDE",
                current_location=target_location,
                reason=f"Auto-reconciled classroom transfer from {prev_room} to {target_location} (Transit: {delta_t:.1f}s)"
            )

        # 5. Normal Valid Transitions
        if dir_norm == "IN":
            st.state = "INSIDE"
            st.location_id = target_location
            st.last_event_time = now
            st.last_direction = "IN"
            return TransitionResult(
                is_valid=True,
                action="ACCEPTED",
                current_state="INSIDE",
                current_location=target_location,
                reason=f"Valid entry into {target_location}"
            )
        else: # OUT
            prev_loc = st.location_id
            st.state = "OUTSIDE"
            st.location_id = "OUTSIDE"
            st.last_event_time = now
            st.last_direction = "OUT"
            return TransitionResult(
                is_valid=True,
                action="ACCEPTED",
                current_state="OUTSIDE",
                current_location="OUTSIDE",
                reason=f"Valid exit from {prev_loc}"
            )
