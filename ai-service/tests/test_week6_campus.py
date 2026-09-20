"""Unit tests verifying Week 6 Campus Orchestration, Reconciler, Priority Scheduler, and Global Presence."""
import pytest
import time
from app.scheduling.priority_scheduler import PriorityInferenceScheduler, PriorityTier
from app.state.global_student_state import GlobalStudentStateManager
from app.events.event_reconciler import EventReconciler
from app.attendance.event import AttendanceEvent
from app.orchestration.campus_manager import CampusManager

def test_priority_scheduler_ordering():
    scheduler = PriorityInferenceScheduler(max_queue_size=10)
    scheduler.schedule(track_id=1, camera_id="CAM_1", crop_data=None, tier=PriorityTier.CONFIRMED_TTL)
    scheduler.schedule(track_id=2, camera_id="CAM_1", crop_data=None, tier=PriorityTier.CRITICAL_BOUNDARY)
    scheduler.schedule(track_id=3, camera_id="CAM_1", crop_data=None, tier=PriorityTier.NEW_TRACK)

    # Highest priority (lowest tier value) should pop first
    t1 = scheduler.get_next_task()
    assert t1.track_id == 2
    assert t1.priority == int(PriorityTier.CRITICAL_BOUNDARY)

    t2 = scheduler.get_next_task()
    assert t2.track_id == 3
    assert t2.priority == int(PriorityTier.NEW_TRACK)

    t3 = scheduler.get_next_task()
    assert t3.track_id == 1
    assert t3.priority == int(PriorityTier.CONFIRMED_TTL)

def test_event_reconciler_anti_flap_and_teleport():
    reconciler = EventReconciler(min_event_interval_sec=2.0)
    now = time.time()

    evt1 = AttendanceEvent("E1", "STU001", "ENTRY_101", "CLASSROOM_101", "IN", now, "2026-09-21T00:00:00", 1, 0.95)
    res1 = reconciler.reconcile(evt1)
    assert not res1.is_conflict
    assert res1.action == "ACCEPTED"

    # Rapid flap: contradictory OUT in <2.0s
    evt2 = AttendanceEvent("E2", "STU001", "EXIT_101", "CLASSROOM_101", "OUT", now + 0.5, "2026-09-21T00:00:00", 1, 0.95)
    res2 = reconciler.reconcile(evt2)
    assert res2.is_conflict
    assert res2.action == "DROPPED_CONTRADICTORY"

    # Teleportation: jumping to CLASSROOM_203 within 3.0s (< 5.0s limit)
    evt3 = AttendanceEvent("E3", "STU001", "ENTRY_203", "CLASSROOM_203", "IN", now + 3.0, "2026-09-21T00:00:00", 2, 0.95)
    res3 = reconciler.reconcile(evt3)
    assert res3.is_conflict
    assert res3.action == "RAPID_FLAP_SUPPRESSED"

def test_global_student_state_manager():
    mgr = GlobalStudentStateManager()
    t0 = time.time()

    # Enter Classroom 101
    s1 = mgr.update_presence("STU001", "CLASSROOM_101", "IN", "ENTRY_101", t0)
    assert s1.state == "INSIDE"
    assert s1.current_location == "CLASSROOM_101"

    # Query occupancy
    assert mgr.get_classroom_occupants("CLASSROOM_101") == ["STU001"]
    assert mgr.get_classroom_occupants("CLASSROOM_203") == []

    # Exit Classroom 101 after 10s
    s2 = mgr.update_presence("STU001", "CLASSROOM_101", "OUT", "EXIT_101", t0 + 10.0)
    assert s2.state == "OUTSIDE"
    assert s2.current_location == "OUTSIDE"
    assert s2.accumulated_inside_sec == pytest.approx(10.0, rel=1e-2)

def test_campus_manager_multi_room_initialization():
    campus = CampusManager("configs/campus/campus_config.json")
    assert len(campus.classrooms) == 5
    assert "CLASSROOM_101" in campus.classrooms
    assert "CLASSROOM_501" in campus.classrooms

    telemetry = campus.get_campus_telemetry()
    assert telemetry["total_classrooms"] == 5
    assert telemetry["total_cameras"] == 10

