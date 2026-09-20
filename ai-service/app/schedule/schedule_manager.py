"""Schedule and Period-Level Attendance Engine for Academic Timetable Compliance."""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime, time as dtime

@dataclass
class PeriodSchedule:
    period_id: str
    subject: str
    start_time: str   # "HH:MM" 24hr format
    end_time: str     # "HH:MM" 24hr format
    min_duration_minutes: int = 30  # Minimum presence required for full attendance

@dataclass
class PeriodAttendanceRecord:
    record_id: str
    date: str
    period_id: str
    subject: str
    student_id: str
    classroom_id: str
    status: str       # "PRESENT", "LATE", "ABSENT", "PARTIAL"
    first_in_time: str
    last_out_time: Optional[str]
    total_minutes_inside: float
    audit_timestamp: str

class ScheduleManager:
    def __init__(self, schedule_file: str = "data/schedules/schedule.json"):
        self.schedule_file = Path(schedule_file)
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        self.schedules: Dict[str, List[PeriodSchedule]] = {}
        self.load_or_seed()

    def load_or_seed(self):
        if self.schedule_file.exists():
            try:
                with open(self.schedule_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for room, periods in data.items():
                        self.schedules[room] = [PeriodSchedule(**p) for p in periods]
                return
            except Exception:
                pass

        # Seed default timetable for CLASSROOM_203
        self.schedules["CLASSROOM_203"] = [
            PeriodSchedule("P1", "VLSI Design", "09:00", "09:50", 25),
            PeriodSchedule("P2", "Embedded Systems", "10:00", "10:50", 25),
            PeriodSchedule("P3", "Digital Signals", "11:00", "11:50", 25),
            PeriodSchedule("P4", "Computer Vision Lab", "13:00", "14:50", 60),
            PeriodSchedule("P5", "Active Academic Session", "00:00", "23:59", 1)  # All-day catch-all for live testing
        ]
        self.save()

    def save(self):
        data = {
            room: [asdict(p) for p in periods]
            for room, periods in self.schedules.items()
        }
        with open(self.schedule_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_active_period(self, classroom_id: str, current_dt: Optional[datetime] = None) -> Optional[PeriodSchedule]:
        if current_dt is None:
            current_dt = datetime.now()
        cur_str = current_dt.strftime("%H:%M")
        periods = self.schedules.get(classroom_id, [])
        for p in periods:
            if p.start_time <= cur_str <= p.end_time:
                return p
        return None
