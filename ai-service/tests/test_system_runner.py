"""Unit tests verifying master system runner orchestration and camera lifecycle."""
import pytest
import time
from app.system_runner import seed_demo_roster, SAMPLE_STUDENTS
from app.backend.api import campus_manager, student_repo, attendance_repo
from app.camera.health_monitor import default_health_monitor
from app.camera.stream_config import CameraConnectionState

def test_system_runner_roster_seeding():
    seed_demo_roster()
    students = student_repo.list_students()
    assert len(students) >= len(SAMPLE_STUDENTS)
    ids = [s.student_id for s in students]
    assert "STU001" in ids
    assert "STU002" in ids

def test_system_runner_campus_lifecycle():
    # 1. Start campus
    campus_manager.start_campus()
    health = default_health_monitor.get_all_health()

    assert len(health) >= 10
    for cid in campus_manager.cameras.keys():
        metrics = health[cid]
        assert metrics["state"] == CameraConnectionState.STREAMING.value
        assert metrics["measured_fps"] == 25.0

    # 2. Stop campus
    campus_manager.stop_campus()
    stopped_health = default_health_monitor.get_all_health()
    for cid in campus_manager.cameras.keys():
        metrics = stopped_health[cid]
        assert metrics["state"] == CameraConnectionState.DISCONNECTED.value
        assert metrics["measured_fps"] == 0.0
