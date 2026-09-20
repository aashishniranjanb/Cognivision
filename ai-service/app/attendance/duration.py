"""Duration Engine tracking real-time student presence duration inside designated premises."""
import time
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class PresenceSession:
    student_id: str
    location_id: str
    entry_time: float
    exit_time: Optional[float] = None
    duration_seconds: float = 0.0
    status: str = "INSIDE"  # "INSIDE", "EXITED"

    @property
    def current_duration_formatted(self) -> str:
        end = self.exit_time if self.exit_time is not None else time.time()
        dur = max(0, int(end - self.entry_time))
        hrs = dur // 3600
        mins = (dur % 3600) // 60
        secs = dur % 60
        if hrs > 0:
            return f"{hrs}h {mins:02d}m {secs:02d}s"
        return f"{mins:02d}m {secs:02d}s"

class DurationEngine:
    def __init__(self):
        # student_id -> current open PresenceSession
        self.active_sessions: Dict[str, PresenceSession] = {}
        # Historical completed sessions
        self.completed_sessions: List[PresenceSession] = []

    def record_entry(self, student_id: str, location_id: str, timestamp: float) -> PresenceSession:
        if student_id in self.active_sessions:
            # Already inside; update location if needed without wiping entry timestamp
            return self.active_sessions[student_id]

        session = PresenceSession(
            student_id=student_id,
            location_id=location_id,
            entry_time=timestamp,
            status="INSIDE"
        )
        self.active_sessions[student_id] = session
        return session

    def record_exit(self, student_id: str, timestamp: float) -> Optional[PresenceSession]:
        if student_id not in self.active_sessions:
            return None

        session = self.active_sessions.pop(student_id)
        session.exit_time = timestamp
        session.duration_seconds = max(0.0, timestamp - session.entry_time)
        session.status = "EXITED"
        self.completed_sessions.append(session)
        return session

    def get_session(self, student_id: str) -> Optional[PresenceSession]:
        return self.active_sessions.get(student_id)
