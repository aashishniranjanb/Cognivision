"""Attendance Event data model representing verified entry/exit biometric occurrences."""
from dataclasses import dataclass, asdict
from typing import Optional, Dict
import time
import json

@dataclass
class AttendanceEvent:
    event_id: str
    student_id: str
    camera_id: str
    location_id: str
    direction: str          # "IN" or "OUT"
    timestamp: float        # Unix epoch in seconds
    timestamp_iso: str      # ISO 8601 formatted string
    track_id: int
    confidence: float       # Fused identity similarity * reliability
    event_type: str = "ATTENDANCE_EVENT"

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
