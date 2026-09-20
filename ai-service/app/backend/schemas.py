"""Pydantic REST API Schemas for Fast responses and dashboard views."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class StudentProfileResponse(BaseModel):
    student_id: str
    name: str
    department: str
    year: int
    current_location: str
    state: str
    entry_time: Optional[float] = None
    last_seen: float
    accumulated_inside_sec: float
    periods: List[Dict[str, Any]] = []

class ClassroomStatusResponse(BaseModel):
    classroom_id: str
    name: str
    capacity: int
    occupancy: int
    occupancy_pct: float
    total_events: int
    entry_camera: str
    exit_camera: str

class CampusSummaryResponse(BaseModel):
    campus_id: str
    total_enrolled: int
    present_campus: int
    outside_campus: int
    total_events: int
    active_classrooms: int

class ManualEventRequest(BaseModel):
    student_id: str
    camera_id: str
    classroom_id: str
    direction: str  # "IN" or "OUT"
    confidence: float = 0.95

