"""Standardized Event Contracts between AI Engine, Event Bus, Persistence, and Dashboard."""
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
from datetime import datetime
import json
import uuid

@dataclass
class CampusEvent:
    event_id: str
    timestamp: float
    timestamp_iso: str
    camera_id: str
    classroom_id: str
    track_id: int
    event_type: str              # "IN", "OUT", "UNKNOWN_PERSON", "LOW_FACE_QUALITY", "IDENTITY_UNCERTAIN"
    confidence: float
    student_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def location_id(self) -> str:
        return self.classroom_id

    @property
    def direction(self) -> str:
        return self.event_type

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def create_attendance(
        cls,
        student_id: str,
        camera_id: str,
        classroom_id: str,
        track_id: int,
        direction: str,
        confidence: float,
        timestamp: Optional[float] = None,
        metadata: Optional[dict] = None
    ) -> "CampusEvent":
        ts = timestamp if timestamp is not None else datetime.now().timestamp()
        iso = datetime.fromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%S")
        return cls(
            event_id=f"EVT_{uuid.uuid4().hex[:8].upper()}",
            timestamp=ts,
            timestamp_iso=iso,
            camera_id=camera_id,
            classroom_id=classroom_id,
            track_id=track_id,
            event_type=direction,  # "IN" or "OUT"
            confidence=confidence,
            student_id=student_id,
            metadata=metadata or {}
        )

    @classmethod
    def create_exception(
        cls,
        anomaly_type: str,
        camera_id: str,
        classroom_id: str,
        track_id: int,
        confidence: float,
        student_id: Optional[str] = None,
        details: Optional[str] = None
    ) -> "CampusEvent":
        ts = datetime.now().timestamp()
        iso = datetime.fromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%S")
        return cls(
            event_id=f"EXC_{uuid.uuid4().hex[:8].upper()}",
            timestamp=ts,
            timestamp_iso=iso,
            camera_id=camera_id,
            classroom_id=classroom_id,
            track_id=track_id,
            event_type=anomaly_type,
            confidence=confidence,
            student_id=student_id,
            metadata={"details": details or ""}
        )

