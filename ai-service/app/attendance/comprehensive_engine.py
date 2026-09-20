"""Comprehensive Attendance & Period Evaluation System with Exception Auditing."""
import time
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.attendance.event import AttendanceEvent
from app.attendance.zone import LineCrossingDetector, VirtualLine
from app.attendance.state import AttendanceStateMachine, AttendanceStatus
from app.attendance.duration import DurationEngine
from app.schedule.schedule_manager import ScheduleManager, PeriodAttendanceRecord
from app.identity.robust_identity import RobustIdentityManager, AnomalyEvent

class ComprehensiveAttendanceEngine:
    def __init__(
        self,
        camera_id: str = "ENTRY_CAM_01",
        classroom_id: str = "CLASSROOM_203",
        event_log_file: str = "data/attendance_records/events.jsonl",
        period_log_file: str = "data/attendance_records/period_attendance.jsonl",
        exception_log_file: str = "data/attendance_records/exceptions.jsonl",
        virtual_line: Optional[VirtualLine] = None
    ):
        self.camera_id = camera_id
        self.classroom_id = classroom_id
        self.event_log_file = Path(event_log_file)
        self.period_log_file = Path(period_log_file)
        self.exception_log_file = Path(exception_log_file)
        for f in [self.event_log_file, self.period_log_file, self.exception_log_file]:
            f.parent.mkdir(parents=True, exist_ok=True)

        if virtual_line is None:
            virtual_line = VirtualLine(pt1=(40, 270), pt2=(920, 270), name="CLASSROOM_BOUNDARY")

        self.crossing_detector = LineCrossingDetector(virtual_line, cooldown_seconds=4.0)
        self.state_machine = AttendanceStateMachine()
        self.duration_engine = DurationEngine()
        self.schedule_manager = ScheduleManager()
        self.identity_manager = RobustIdentityManager(confirm_threshold=0.50, min_confirmed_hits=2)

        # In-memory recent feeds for HUD
        self.recent_events: List[AttendanceEvent] = []
        self.recent_period_records: List[PeriodAttendanceRecord] = []
        self.recent_exceptions: List[AnomalyEvent] = []

    def process_frame_observation(
        self,
        track_id: int,
        raw_face_candidate_id: Optional[str],
        face_similarity: float,
        face_reliability: float,
        centroid: Tuple[int, int]
    ) -> Tuple[str, Optional[str], Optional[AttendanceEvent]]:
        """
        Processes single frame track observation:
        1. Updates robust identity state
        2. Evaluates spatial boundary crossing
        3. Generates deduplicated attendance events
        4. Calculates period-level compliance
        """
        # 1. Update Robust Identity with Reliability Weighting
        status, confirmed_id, confidence = self.identity_manager.update_observation(
            track_id=track_id,
            candidate_id=raw_face_candidate_id,
            similarity=face_similarity,
            reliability=face_reliability
        )

        # 2. Check Boundary Crossing
        direction = self.crossing_detector.check_crossing(track_id, centroid)
        if direction is None:
            return status, confirmed_id, None

        # 3. Only CONFIRMED students generate audited attendance records
        if status != "CONFIRMED" or confirmed_id is None:
            self._log_exception("UNCONFIRMED_CROSSING", track_id, f"Track crossed {direction} while state is {status}")
            return status, confirmed_id, None

        now = time.time()
        now_dt = datetime.fromtimestamp(now)
        iso_str = now_dt.strftime("%Y-%m-%dT%H:%M:%S")
        evt_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"

        event = AttendanceEvent(
            event_id=evt_id,
            student_id=confirmed_id,
            camera_id=self.camera_id,
            location_id=self.classroom_id,
            direction=direction,
            timestamp=now,
            timestamp_iso=iso_str,
            track_id=track_id,
            confidence=confidence
        )

        # 4. State & Duration Update
        self.state_machine.transition_on_event(
            student_id=confirmed_id,
            direction=direction,
            location_id=self.classroom_id,
            timestamp=now
        )

        if direction == "IN":
            self.duration_engine.record_entry(confirmed_id, self.classroom_id, now)
        elif direction == "OUT":
            session = self.duration_engine.record_exit(confirmed_id, now)
            # Evaluate Period Attendance when exiting or when period concludes
            if session:
                self._evaluate_period_attendance(confirmed_id, session.entry_time, session.exit_time, now_dt)

        self._audit_log_event(event)
        self.recent_events.append(event)
        if len(self.recent_events) > 10:
            self.recent_events.pop(0)

        return status, confirmed_id, event

    def _evaluate_period_attendance(self, student_id: str, entry_ts: float, exit_ts: float, current_dt: datetime):
        active_period = self.schedule_manager.get_active_period(self.classroom_id, current_dt)
        if not active_period:
            return

        dur_mins = (exit_ts - entry_ts) / 60.0
        status = "PRESENT" if dur_mins >= (active_period.min_duration_minutes * 0.5) else "PARTIAL"

        rec = PeriodAttendanceRecord(
            record_id=f"PER-{uuid.uuid4().hex[:8].upper()}",
            date=current_dt.strftime("%Y-%m-%d"),
            period_id=active_period.period_id,
            subject=active_period.subject,
            student_id=student_id,
            classroom_id=self.classroom_id,
            status=status,
            first_in_time=datetime.fromtimestamp(entry_ts).strftime("%H:%M:%S"),
            last_out_time=datetime.fromtimestamp(exit_ts).strftime("%H:%M:%S"),
            total_minutes_inside=round(dur_mins, 1),
            audit_timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        )

        try:
            with open(self.period_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec.__dict__) + "\n")
            self.recent_period_records.append(rec)
            if len(self.recent_period_records) > 10:
                self.recent_period_records.pop(0)
        except Exception as e:
            print(f"[AttendanceEngine] Period log error: {e}")

    def _log_exception(self, exc_type: str, track_id: int, details: str):
        evt = AnomalyEvent(exc_type, track_id, time.time(), details)
        self.recent_exceptions.append(evt)
        try:
            with open(self.exception_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(evt.__dict__) + "\n")
        except Exception:
            pass

    def _audit_log_event(self, event: AttendanceEvent):
        try:
            with open(self.event_log_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            print(f"[AttendanceEngine] Audit log error: {e}")
