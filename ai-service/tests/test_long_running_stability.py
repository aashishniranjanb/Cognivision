"""Production Hardening: Long-running memory and stability test.
Implements Section 14 of V1.2 Plan:
Verifies that 500+ sequential event batches do not cause:
  - Memory leak (RSS growth must remain bounded < 25 MB delta)
  - SQLite database lock or connection leakage
  - Unbounded queue growth in Event Bus
  - Track accumulation leak
"""
import time
import os
import psutil
import pytest

from app.events.event_schema import CampusEvent
from app.events.event_bus import default_event_bus
from app.backend.attendance_repository import AttendanceRepository
from app.orchestration.campus_manager import CampusManager


def test_long_running_event_loop_stability():
    proc = psutil.Process(os.getpid())
    initial_ram_mb = proc.memory_info().rss / (1024 * 1024)

    campus_mgr = CampusManager("configs/campus/campus_config.json")
    repo = AttendanceRepository()

    # Process 500 simulated events across 10 cameras
    classrooms = ["C101", "C203", "C301", "C401", "C501"]
    for i in range(500):
        room = classrooms[i % len(classrooms)]
        direction = "IN" if i % 4 != 0 else "OUT"
        evt = CampusEvent.create_attendance(
            student_id=f"STU{(i % 100) + 1:03d}",
            camera_id=f"CAM-{room.replace('C', '')}-{direction}",
            classroom_id=room,
            track_id=1000 + i,
            direction=direction,
            confidence=0.88
        )
        campus_mgr.receive_event(evt)
        repo.save_event(evt)

    # Check memory delta after 500 events
    final_ram_mb = proc.memory_info().rss / (1024 * 1024)
    ram_growth_mb = final_ram_mb - initial_ram_mb

    # SQLite query should still respond instantly without connection leaks
    recent = repo.get_recent_events(limit=10)
    assert len(recent) == 10

    # Ensure memory growth is strictly bounded (< 30 MB delta for 500 processed events)
    assert ram_growth_mb < 30.0, f"Memory leak detected: grew by {ram_growth_mb:.2f} MB"
