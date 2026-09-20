"""Classroom Manager: Coordinates paired Entry and Exit CameraWorkers for a physical classroom."""
from typing import Dict, List, Optional, Callable
from app.orchestration.camera_worker import CameraWorker
from app.attendance.event import AttendanceEvent

class ClassroomManager:
    def __init__(
        self,
        classroom_id: str,
        name: str,
        capacity: int = 100,
        entry_config: Optional[dict] = None,
        exit_config: Optional[dict] = None,
        campus_event_bus: Optional[Callable[[AttendanceEvent], None]] = None
    ):
        self.classroom_id = classroom_id
        self.name = name
        self.capacity = capacity
        self.campus_event_bus = campus_event_bus

        # Initialize Entry and Exit Camera Workers
        entry_cfg = entry_config or {"id": f"ENTRY_{classroom_id}", "source": "mock", "direction": "IN", "line_y": 180}
        exit_cfg = exit_config or {"id": f"EXIT_{classroom_id}", "source": "mock", "direction": "OUT", "line_y": 180}

        self.entry_worker = CameraWorker(
            camera_id=entry_cfg.get("id", f"ENTRY_{classroom_id}"),
            classroom_id=classroom_id,
            source_target=entry_cfg.get("source", "mock"),
            direction="IN",
            line_y=entry_cfg.get("line_y", 180),
            event_callback=self._handle_worker_event
        )

        self.exit_worker = CameraWorker(
            camera_id=exit_cfg.get("id", f"EXIT_{classroom_id}"),
            classroom_id=classroom_id,
            source_target=exit_cfg.get("source", "mock"),
            direction="OUT",
            line_y=exit_cfg.get("line_y", 180),
            event_callback=self._handle_worker_event
        )

        # Classroom local presence registry
        self.present_students: set[str] = set()
        self.events_log: List[AttendanceEvent] = []

    def _handle_worker_event(self, event: AttendanceEvent):
        """Internal callback when entry or exit worker detects a confirmed crossing."""
        if event.direction == "IN":
            self.present_students.add(event.student_id)
        elif event.direction == "OUT":
            self.present_students.discard(event.student_id)

        self.events_log.append(event)
        
        # Propagate upstream to campus manager
        if self.campus_event_bus:
            self.campus_event_bus(event)

    def start(self):
        self.entry_worker.start()
        self.exit_worker.start()

    def stop(self):
        self.entry_worker.stop()
        self.exit_worker.stop()

    def get_occupancy(self) -> int:
        return len(self.present_students)

    def get_occupancy_ratio(self) -> float:
        return len(self.present_students) / max(1, self.capacity)

    def get_status(self) -> dict:
        return {
            "classroom_id": self.classroom_id,
            "name": self.name,
            "capacity": self.capacity,
            "occupancy": len(self.present_students),
            "occupancy_pct": round(self.get_occupancy_ratio() * 100.0, 1),
            "total_events": len(self.events_log),
            "entry_camera": self.entry_worker.camera_id,
            "exit_camera": self.exit_worker.camera_id
        }
