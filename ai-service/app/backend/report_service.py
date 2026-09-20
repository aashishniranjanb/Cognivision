"""Period Attendance Engine 2.0 & Automated Campus Attendance Reporting Service."""
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime, time as dtime
import json

from app.backend.attendance_repository import AttendanceRepository
from app.backend.student_repository import StudentRepository
from app.state.global_student_state import GlobalStudentStateManager

@dataclass
class PeriodRecord:
    student_id: str
    period_id: str
    classroom_id: str
    scheduled_start: str
    scheduled_end: str
    first_seen: Optional[str]
    last_seen: Optional[str]
    duration_seconds: float
    attendance_status: str     # "PRESENT", "PARTIAL", "ABSENT", "UNCERTAIN"

    def to_dict(self) -> dict:
        return asdict(self)

class ReportService:
    def __init__(
        self,
        attendance_repo: Optional[AttendanceRepository] = None,
        student_repo: Optional[StudentRepository] = None,
        state_mgr: Optional[GlobalStudentStateManager] = None,
        min_present_ratio: float = 0.60
    ):
        self.attendance_repo = attendance_repo or AttendanceRepository()
        self.student_repo = student_repo or StudentRepository()
        self.state_mgr = state_mgr or GlobalStudentStateManager()
        self.min_present_ratio = min_present_ratio

        # Standard academic timetable definition
        self.period_schedules = [
            {"period_id": "P1", "start": "09:00", "end": "09:50", "subject": "VLSI Design & Embedded Systems"},
            {"period_id": "P2", "start": "10:00", "end": "10:50", "subject": "Signals & DSP Lecture"},
            {"period_id": "P3", "start": "11:00", "end": "11:50", "subject": "Computer Vision & Deep Learning"},
            {"period_id": "P4", "start": "13:00", "end": "13:50", "subject": "Robotics & Microcontrollers"}
        ]

    def evaluate_student_period_attendance(
        self,
        student_id: str,
        classroom_id: str = "CLASSROOM_203",
        date_str: Optional[str] = None
    ) -> List[PeriodRecord]:
        """Evaluates exact period attendance based on presence duration vs minimum threshold."""
        events = self.attendance_repo.get_student_events(student_id)
        results: List[PeriodRecord] = []

        # Current live state for duration calculation
        st = self.state_mgr.get_or_create(student_id)
        total_duration = st.accumulated_inside_sec

        for sched in self.period_schedules:
            p_id = sched["period_id"]
            scheduled_sec = 50 * 60.0 # 50 minutes = 3000s

            # Determine attendance decision based on audited presence duration
            if total_duration >= (scheduled_sec * self.min_present_ratio):
                status = "PRESENT"
            elif total_duration >= (scheduled_sec * 0.20):
                status = "PARTIAL"
            elif total_duration > 0:
                status = "UNCERTAIN"
            else:
                status = "ABSENT"

            first_seen_iso = None
            last_seen_iso = None
            if events:
                first_seen_iso = events[0].get("timestamp_iso", "")
                last_seen_iso = events[-1].get("timestamp_iso", "")

            rec = PeriodRecord(
                student_id=student_id,
                period_id=p_id,
                classroom_id=classroom_id,
                scheduled_start=sched["start"],
                scheduled_end=sched["end"],
                first_seen=first_seen_iso,
                last_seen=last_seen_iso,
                duration_seconds=round(total_duration, 1),
                attendance_status=status
            )
            results.append(rec)

        return results

    def generate_classroom_daily_report(self, classroom_id: str) -> dict:
        """Generates full classroom summary report with roster breakdown."""
        occupants = self.state_mgr.get_classroom_occupants(classroom_id)
        students = self.student_repo.list_students()

        roster_summary = []
        for s in students:
            periods = self.evaluate_student_period_attendance(s.student_id, classroom_id=classroom_id)
            is_inside = s.student_id in occupants
            roster_summary.append({
                "student_id": s.student_id,
                "name": s.name,
                "department": s.department,
                "is_present_now": is_inside,
                "periods": [p.to_dict() for p in periods]
            })

        return {
            "classroom_id": classroom_id,
            "generated_at": datetime.now().isoformat(),
            "total_enrolled": len(students),
            "currently_inside": len(occupants),
            "roster": roster_summary
        }

