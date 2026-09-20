"""Unit Tests verifying Event Bus, Event Schema, Repositories, Report Engine, and Camera Health Monitor."""
import pytest
import time
from app.events.event_schema import CampusEvent
from app.events.event_bus import CampusEventBus
from app.backend.attendance_repository import AttendanceRepository
from app.backend.student_repository import StudentRepository
from app.backend.report_service import ReportService
from app.camera.stream_config import CameraStreamConfig, CameraConnectionState
from app.camera.reconnect import ReconnectPolicy
from app.camera.health_monitor import CameraHealthMonitor

def test_campus_event_creation():
    evt = CampusEvent.create_attendance(
        student_id="STU001",
        camera_id="C203_ENTRY",
        classroom_id="CLASSROOM_203",
        track_id=12,
        direction="IN",
        confidence=0.94
    )
    assert evt.student_id == "STU001"
    assert evt.event_type == "IN"
    assert evt.classroom_id == "CLASSROOM_203"
    assert evt.confidence == 0.94

    exc = CampusEvent.create_exception(
        anomaly_type="UNKNOWN_PERSON",
        camera_id="C203_EXIT",
        classroom_id="CLASSROOM_203",
        track_id=45,
        confidence=0.22
    )
    assert exc.event_type == "UNKNOWN_PERSON"
    assert exc.student_id is None

def test_event_bus_sync_publish():
    bus = CampusEventBus()
    received = []

    bus.subscribe("IN", lambda e: received.append(e))
    evt_in = CampusEvent.create_attendance("STU001", "CAM_1", "ROOM_1", 1, "IN", 0.95)
    evt_out = CampusEvent.create_attendance("STU001", "CAM_2", "ROOM_1", 1, "OUT", 0.95)

    bus.publish(evt_in)
    bus.publish(evt_out)

    assert len(received) == 1
    assert received[0].event_type == "IN"

def test_attendance_repository_sqlite(tmp_path):
    db_file = tmp_path / "test_att.db"
    audit_file = tmp_path / "audit.jsonl"
    repo = AttendanceRepository(db_path=str(db_file), audit_file=str(audit_file))

    evt = CampusEvent.create_attendance("STU002", "CAM_1", "CLASS_101", 3, "IN", 0.89)
    repo.save_event(evt)

    recent = repo.get_recent_events(limit=5)
    assert len(recent) == 1
    assert recent[0]["student_id"] == "STU002"
    assert recent[0]["event_type"] == "IN"

    student_evts = repo.get_student_events("STU002")
    assert len(student_evts) == 1

def test_period_report_service(tmp_path):
    db_file = tmp_path / "test_report.db"
    audit_file = tmp_path / "audit.jsonl"
    repo = AttendanceRepository(db_path=str(db_file), audit_file=str(audit_file))
    report_svc = ReportService(attendance_repo=repo)

    records = report_svc.evaluate_student_period_attendance("STU001")
    assert len(records) == 4
    assert records[0].period_id == "P1"
    # Initial status without duration should be ABSENT
    assert records[0].attendance_status == "ABSENT"

def test_reconnect_policy():
    policy = ReconnectPolicy(base_delay_sec=0.05, max_delay_sec=0.2, backoff_factor=2.0, max_attempts=3)
    assert policy.can_reconnect()
    policy.record_attempt()
    assert not policy.can_reconnect() # Delay not elapsed
    time.sleep(0.06)
    assert policy.can_reconnect()

def test_camera_health_monitor():
    monitor = CameraHealthMonitor()
    rec = monitor.update_metrics(
        camera_id="C203_ENTRY",
        state=CameraConnectionState.STREAMING,
        fps=25.0,
        dropped=0,
        queue_size=2,
        latency_ms=18.5,
        reconnects=0
    )
    assert rec.state == CameraConnectionState.STREAMING
    assert rec.measured_fps == 25.0
    assert monitor.get_health("C203_ENTRY") is not None

