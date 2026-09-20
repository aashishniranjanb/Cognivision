"""Campus Manager: Multi-Classroom Orchestrator managing 5 classrooms, 10 camera streams,
cross-camera event reconciliation, and unified global student presence state.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.orchestration.classroom_manager import ClassroomManager
from app.events.event_reconciler import EventReconciler, ConflictResolution
from app.state.global_student_state import GlobalStudentStateManager, GlobalStudentState
from app.attendance.event import AttendanceEvent

class CampusManager:
    def __init__(self, config_path: str = "configs/campus/campus_config.json"):
        self.config_path = Path(config_path)
        self.campus_id = "CAMPUS_DEFAULT"
        self.classrooms: Dict[str, ClassroomManager] = {}

        # Core Campus Invariants & Single Source of Truth
        self.reconciler = EventReconciler(min_event_interval_sec=2.0)
        self.state_manager = GlobalStudentStateManager()

        # Telemetry & Auditing
        self.accepted_events: List[AttendanceEvent] = []
        self.rejected_events: List[dict] = []

        self._load_configuration()

    def _load_configuration(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Campus configuration file not found at: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)

        self.campus_id = cfg.get("campus_id", "CAMPUS_DEFAULT")
        for room in cfg.get("classrooms", []):
            cid = room["id"]
            c_name = room.get("name", cid)
            c_cap = room.get("capacity", 100)
            cams = room.get("cameras", {})

            entry_cfg = cams.get("entry")
            exit_cfg = cams.get("exit")

            mgr = ClassroomManager(
                classroom_id=cid,
                name=c_name,
                capacity=c_cap,
                entry_config=entry_cfg,
                exit_config=exit_cfg,
                campus_event_bus=self.receive_event
            )
            self.classrooms[cid] = mgr

    def start_campus(self):
        """Starts all camera workers across all configured classrooms."""
        for c in self.classrooms.values():
            c.start()

    def stop_campus(self):
        """Gracefully halts all camera workers."""
        for c in self.classrooms.values():
            c.stop()

    def receive_event(self, event: AttendanceEvent) -> ConflictResolution:
        """Central event bus: Reconciles incoming events against contradictory flapping & impossible transitions."""
        resolution = self.reconciler.reconcile(event)

        if resolution.action == "ACCEPTED":
            # Update single source of campus presence
            self.state_manager.update_presence(
                student_id=event.student_id,
                location_id=event.location_id,
                direction=event.direction,
                camera_id=event.camera_id,
                timestamp=event.timestamp
            )
            self.accepted_events.append(event)
        else:
            self.rejected_events.append({
                "event": event.to_dict(),
                "reason": resolution.reason,
                "action": resolution.action,
                "rejected_at": time.time()
            })

        return resolution

    def get_campus_telemetry(self) -> dict:
        summary = self.state_manager.get_campus_summary()
        room_telemetry = {cid: mgr.get_status() for cid, mgr in self.classrooms.items()}
        return {
            "campus_id": self.campus_id,
            "total_classrooms": len(self.classrooms),
            "total_cameras": len(self.classrooms) * 2,
            "accepted_events": len(self.accepted_events),
            "rejected_conflicts": len(self.rejected_events),
            "summary": summary,
            "classrooms": room_telemetry
        }
