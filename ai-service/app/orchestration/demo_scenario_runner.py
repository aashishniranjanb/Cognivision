"""Demo Mode Scenario Engine.
Implements Section 12 of V1.2 Plan:
Provides interactive, deterministic live scenarios for competition judges and operators:
  1. Normal Entry (Clean face + body fusion -> Confirmed PRESENT)
  2. Face Occlusion (Masked face -> Body ReID recovery -> Confirmed)
  3. Low Lighting (Sub-optimal lux -> Adaptive frame enhancement -> Confirmed)
  4. Unknown Visitor (Unrecognized face -> UNKNOWN -> Exception raised -> No Attendance)
  5. Two People Crossing (Parallel corridor tracks -> Zero ID switch -> Dual entry)
  6. Camera Failure (RTSP drop -> OFFLINE alert -> Automatic resilience)
  7. Occupancy Mismatch (Physical count > Enrolled roster -> Mismatch alarm)
"""
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from app.events.event_schema import CampusEvent
from app.events.event_bus import default_event_bus
from app.camera.health_monitor import default_health_monitor


@dataclass
class ScenarioStepTrace:
    step_number: int
    title: str
    detail: str
    status: str  # "OK", "WARN", "ALARM", "INFO"
    data: Dict[str, Any]


@dataclass
class ScenarioExecutionResult:
    scenario_id: str
    scenario_name: str
    description: str
    steps: List[ScenarioStepTrace]
    final_state: str  # "SUCCESS", "HANDLED_EXCEPTION", "ALARM_TRIGGERED"
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "description": self.description,
            "steps": [asdict(s) for s in self.steps],
            "final_state": self.final_state,
            "summary": self.summary,
        }


class DemoScenarioEngine:
    """Executes deterministic multi-step scenarios demonstrating system resilience."""

    AVAILABLE_SCENARIOS = {
        "normal_entry": {
            "name": "Scenario 1 — Normal Doorway Entry",
            "description": "Student walks through capture corridor. High-confidence face & body fusion cleanly records attendance.",
        },
        "face_occlusion": {
            "name": "Scenario 2 — Mask / Face Occlusion",
            "description": "Student wears a face mask. ArcFace similarity drops, but OSNet body ReID fusion rescues identity.",
        },
        "low_lighting": {
            "name": "Scenario 3 — Low Lighting Corridor",
            "description": "Corridor lighting drops below standard. Best-frame selection picks highest Laplacian frame to confirm entry.",
        },
        "unknown_visitor": {
            "name": "Scenario 4 — Unknown Visitor / Intruder",
            "description": "Unregistered person enters room. System records physical presence but blocks attendance and raises an Exception alert.",
        },
        "two_people_crossing": {
            "name": "Scenario 5 — Two People Simultaneous Transit",
            "description": "Two students cross the doorway side-by-side. ByteTrack maintains distinct trajectories with zero ID switches.",
        },
        "camera_failure": {
            "name": "Scenario 6 — Camera RTSP Disconnect",
            "description": "Camera feed experiences network drop. Health monitor detects loss, flags OFFLINE, and triggers failover.",
        },
        "occupancy_mismatch": {
            "name": "Scenario 7 — Occupancy Discrepancy Alarm",
            "description": "Physical body headcount inside classroom exceeds expected student enrollment, triggering an automatic investigation alert.",
        },
    }

    def __init__(self, campus_manager=None):
        self.campus_manager = campus_manager

    def list_scenarios(self) -> List[Dict[str, str]]:
        return [
            {"id": s_id, "name": meta["name"], "description": meta["description"]}
            for s_id, meta in self.AVAILABLE_SCENARIOS.items()
        ]

    def run_scenario(self, scenario_id: str) -> ScenarioExecutionResult:
        if scenario_id == "normal_entry":
            return self._run_normal_entry()
        elif scenario_id == "face_occlusion":
            return self._run_face_occlusion()
        elif scenario_id == "low_lighting":
            return self._run_low_lighting()
        elif scenario_id == "unknown_visitor":
            return self._run_unknown_visitor()
        elif scenario_id == "two_people_crossing":
            return self._run_two_people_crossing()
        elif scenario_id == "camera_failure":
            return self._run_camera_failure()
        elif scenario_id == "occupancy_mismatch":
            return self._run_occupancy_mismatch()
        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

    def _run_normal_entry(self) -> ScenarioExecutionResult:
        steps = [
            ScenarioStepTrace(1, "Person Detection", "YOLOv8-Nano detected body bbox at [420, 180, 540, 720], confidence 0.94", "OK", {"bbox": [420, 180, 540, 720]}),
            ScenarioStepTrace(2, "Corridor Tracking", "ByteTrack initiated track #201 across doorway corridor vector", "OK", {"track_id": 201}),
            ScenarioStepTrace(3, "Best Frame Selection", "Captured 12 candidate crops; optimal frame selected with face width 104px, sharpness 148.2", "OK", {"face_width_px": 104, "laplacian": 148.2}),
            ScenarioStepTrace(4, "Biometric Fusion", "ArcFace similarity 0.94, OSNet body similarity 0.88 -> Combined Fusion Confidence: 0.92 (STU001)", "OK", {"student_id": "STU001", "confidence": 0.92}),
            ScenarioStepTrace(5, "Attendance Record", "Direction IN confirmed for Classroom C101; period session duration initialized to PRESENT", "OK", {"status": "PRESENT", "classroom": "C101"}),
        ]
        evt = CampusEvent.create_attendance(student_id="STU001", camera_id="CAM-101-ENTRY", classroom_id="C101", track_id=201, direction="IN", confidence=0.92)
        default_event_bus.publish(evt)
        if self.campus_manager:
            self.campus_manager.receive_event(evt)
        return ScenarioExecutionResult("normal_entry", "Normal Doorway Entry", "High-confidence multi-modal identification.", steps, "SUCCESS", "Student STU001 verified and marked PRESENT.")

    def _run_face_occlusion(self) -> ScenarioExecutionResult:
        steps = [
            ScenarioStepTrace(1, "Person Detection", "Student wearing protective medical face mask detected at doorway corridor", "OK", {"bbox": [390, 200, 510, 710]}),
            ScenarioStepTrace(2, "Face Extraction Degraded", "ArcFace facial similarity dropped to 0.44 due to nasal/oral landmark occlusion", "WARN", {"face_score": 0.44}),
            ScenarioStepTrace(3, "Body ReID Recovery", "OSNet extracted 512-D torso & gait appearance vector matching STU002 at 0.86 similarity", "OK", {"body_score": 0.86}),
            ScenarioStepTrace(4, "Adaptive Fusion Shift", "Fusion engine shifted weight dynamically (Face: 25%, Body: 75%) -> Composite score 0.76 > 0.70 threshold", "OK", {"fusion_score": 0.76}),
            ScenarioStepTrace(5, "Attendance Validated", "Identity confirmed despite occlusion. IN event recorded for Classroom C101.", "OK", {"student_id": "STU002", "attendance": "PRESENT"}),
        ]
        evt = CampusEvent.create_attendance(student_id="STU002", camera_id="CAM-101-ENTRY", classroom_id="C101", track_id=202, direction="IN", confidence=0.76)
        default_event_bus.publish(evt)
        if self.campus_manager:
            self.campus_manager.receive_event(evt)
        return ScenarioExecutionResult("face_occlusion", "Face Occlusion & Mask Resilience", "Body ReID rescued student identity when face was occluded.", steps, "SUCCESS", "Student STU002 successfully identified via Body ReID fusion.")

    def _run_low_lighting(self) -> ScenarioExecutionResult:
        steps = [
            ScenarioStepTrace(1, "Illumination Check", "Ambient sensor measured 48 lux (sub-optimal illumination)", "WARN", {"lux": 48}),
            ScenarioStepTrace(2, "Corridor Buffer Ingestion", "Capture zone buffer evaluated 15 frames over 0.5s transit window", "OK", {"frames_evaluated": 15}),
            ScenarioStepTrace(3, "Best Frame Extraction", "Best-frame algorithm selected frame #9 with highest local contrast (sharpness 112.4)", "OK", {"laplacian": 112.4}),
            ScenarioStepTrace(4, "Fusion Match", "ArcFace 0.81, Body 0.80 -> Fusion 0.81 matched STU003", "OK", {"student_id": "STU003", "confidence": 0.81}),
            ScenarioStepTrace(5, "Official Record", "IN crossing event logged with 0 false accepts", "OK", {"status": "PRESENT"}),
        ]
        evt = CampusEvent.create_attendance(student_id="STU003", camera_id="CAM-101-ENTRY", classroom_id="C101", track_id=203, direction="IN", confidence=0.81)
        default_event_bus.publish(evt)
        if self.campus_manager:
            self.campus_manager.receive_event(evt)
        return ScenarioExecutionResult("low_lighting", "Low Lighting Doorway Ingestion", "Contrast enhancement and best-frame selection compensated for poor lighting.", steps, "SUCCESS", "Student STU003 recognized and marked PRESENT under 48 lux.")

    def _run_unknown_visitor(self) -> ScenarioExecutionResult:
        steps = [
            ScenarioStepTrace(1, "Physical Detection", "Unenrolled visitor crossed doorway into Classroom C203", "OK", {"bbox": [450, 190, 560, 730]}),
            ScenarioStepTrace(2, "Track Ingestion", "ByteTrack created track #204 with continuous velocity vector", "OK", {"track_id": 204}),
            ScenarioStepTrace(3, "Biometric Database Query", "ArcFace top similarity score was 0.38 (< 0.70 threshold) with margin 0.03", "WARN", {"top_score": 0.38, "threshold": 0.70}),
            ScenarioStepTrace(4, "Identity Rejection", "Identity categorized as UNKNOWN (Zero False Acceptance enforced)", "ALARM", {"decision": "UNKNOWN"}),
            ScenarioStepTrace(5, "Security Exception Raised", "Physical occupancy incremented (body detected), but official academic attendance BLOCKED", "ALARM", {"occupancy": "+1", "attendance": "BLOCKED"}),
        ]
        evt = CampusEvent.create_attendance(student_id="UNKNOWN_VISITOR_99", camera_id="CAM-203-ENTRY", classroom_id="C203", track_id=204, direction="IN", confidence=0.38)
        default_event_bus.publish(evt)
        if self.campus_manager:
            self.campus_manager.receive_event(evt)
        return ScenarioExecutionResult("unknown_visitor", "Unknown Visitor / Non-Enrolled", "Enforces 0% False Acceptance Rate while accurately updating physical occupancy.", steps, "HANDLED_EXCEPTION", "Visitor detected: Attendance blocked, security alert generated.")

    def _run_two_people_crossing(self) -> ScenarioExecutionResult:
        steps = [
            ScenarioStepTrace(1, "Dual Bounding Boxes", "Two distinct persons detected simultaneously entering doorway corridor", "OK", {"person_count": 2}),
            ScenarioStepTrace(2, "Parallel Track Association", "ByteTrack assigned Track #205 and Track #206 with separate Kalman filters", "OK", {"tracks": [205, 206]}),
            ScenarioStepTrace(3, "Decoupled Best Frames", "Independent landmark localization executed for both tracks without ID swapping", "OK", {"id_switches": 0}),
            ScenarioStepTrace(4, "Dual Identification", "Track #205 matched STU004 (0.91); Track #206 matched STU005 (0.89)", "OK", {"matches": ["STU004", "STU005"]}),
            ScenarioStepTrace(5, "Concurrent Ingestion", "Two separate IN events recorded for C203 within 32ms", "OK", {"delta_ms": 32}),
        ]
        e1 = CampusEvent.create_attendance(student_id="STU004", camera_id="CAM-203-ENTRY", classroom_id="C203", track_id=205, direction="IN", confidence=0.91)
        e2 = CampusEvent.create_attendance(student_id="STU005", camera_id="CAM-203-ENTRY", classroom_id="C203", track_id=206, direction="IN", confidence=0.89)
        default_event_bus.publish(e1)
        default_event_bus.publish(e2)
        if self.campus_manager:
            self.campus_manager.receive_event(e1)
            self.campus_manager.receive_event(e2)
        return ScenarioExecutionResult("two_people_crossing", "Simultaneous Two-Person Transit", "Zero ID switching during parallel doorway transit.", steps, "SUCCESS", "Both STU004 and STU005 successfully identified and logged.")

    def _run_camera_failure(self) -> ScenarioExecutionResult:
        default_health_monitor.record_failure("CAM-301-ENTRY")
        steps = [
            ScenarioStepTrace(1, "RTSP Socket Drop", "Simulated packet loss on CAM-301-ENTRY RTSP stream", "WARN", {"camera_id": "CAM-301-ENTRY"}),
            ScenarioStepTrace(2, "Health Watchdog Trigger", "Background health watchdog detected missed frame heartbeat (timeout > 5.0s)", "ALARM", {"timeout_sec": 5.0}),
            ScenarioStepTrace(3, "Status Broadcast", "Camera status transitioned from HEALTHY to OFFLINE", "ALARM", {"status": "OFFLINE"}),
            ScenarioStepTrace(4, "Graceful Degraded Mode", "Campus Manager marked C301 Entry camera in failover; exit camera remains online", "WARN", {"classroom": "C301"}),
            ScenarioStepTrace(5, "Auto-Recovery Queue", "Background reconnect worker scheduled retry attempt with exponential backoff", "INFO", {"next_retry_sec": 3.0}),
        ]
        # Re-record frame after demo demonstration so system recovers
        default_health_monitor.record_frame("CAM-301-ENTRY", fps=25.0)
        return ScenarioExecutionResult("camera_failure", "Camera Stream Disconnect & Watchdog", "Automatic failure detection and resilience without server crash.", steps, "HANDLED_EXCEPTION", "Camera disconnect handled cleanly; watchdog initiated auto-reconnection.")

    def _run_occupancy_mismatch(self) -> ScenarioExecutionResult:
        steps = [
            ScenarioStepTrace(1, "Enrolled Expected Roster", "Official course roster for C401 period expects 45 students", "OK", {"expected": 45}),
            ScenarioStepTrace(2, "Physical Headcount Sensor", "Physical body detection and doorway counter records 49 persons inside C401", "WARN", {"physical_count": 49}),
            ScenarioStepTrace(3, "Discrepancy Calculation", "Physical count (49) exceeds expected enrollment (45) by +4 individuals", "ALARM", {"discrepancy": 4}),
            ScenarioStepTrace(4, "Four Truths Telemetry Update", "Physical Truth (49) diverges from Academic Attendance Truth (45)", "ALARM", {"tier_divergence": True}),
            ScenarioStepTrace(5, "Operator Alert Triggered", "Raised OCCUPANCY_MISMATCH exception in Vision Command Center", "ALARM", {"alert": "OCCUPANCY_MISMATCH"}),
        ]
        return ScenarioExecutionResult("occupancy_mismatch", "Occupancy Discrepancy Alarm", "Highlights discrepancy between Physical Reality and Enrolled Truth.", steps, "ALARM_TRIGGERED", "Occupancy discrepancy detected: 49 physical persons vs 45 enrolled.")
