"""Unit tests for Step 6 — Attendance Reconciliation & Multi-Session Tracking (Plan 24)."""
import pytest
from app.attendance.attendance_reconciler import AttendanceReconciler, PresenceInterval

def test_single_session_present():
    """Plan 24: P1 = 09:00-09:50 (3000s). IN 09:02 (+120s), OUT 09:45 (+2700s) -> 43 min = 86% -> PRESENT."""
    reconciler = AttendanceReconciler(present_ratio_threshold=0.75, partial_ratio_threshold=0.15)
    t0 = 100000.0
    period_start = t0
    period_end = t0 + 3000.0  # 50 min

    # Student enters at 09:02 and exits at 09:45 (2580 seconds)
    reconciler.record_transition("STU001", "IN", "CLASSROOM_203", t0 + 120.0, confidence=0.92)
    reconciler.record_transition("STU001", "OUT", "CLASSROOM_203", t0 + 2700.0, confidence=0.92)

    decision = reconciler.evaluate_student("STU001", "P1", period_start, period_end, "CLASSROOM_203")
    assert decision.status == "PRESENT"
    assert decision.sessions_count == 1
    assert decision.total_presence_seconds == 2580.0
    assert abs(decision.presence_ratio - (2580.0 / 3000.0)) < 1e-4

def test_temporary_exit_and_reentry():
    """Plan 24 Step 6.2:
    09:02 IN, 09:20 OUT (18m = 1080s)
    09:25 IN, 09:48 OUT (23m = 1380s)
    Total presence = 41m (2460s) / 50m = 82% -> PRESENT
    """
    reconciler = AttendanceReconciler(present_ratio_threshold=0.75, partial_ratio_threshold=0.15)
    t0 = 200000.0
    period_start = t0
    period_end = t0 + 3000.0  # 50 min

    # Session 1: 09:02 to 09:20 (18 min = 1080s)
    reconciler.record_transition("STU001", "IN", "CLASSROOM_203", t0 + 120.0)
    reconciler.record_transition("STU001", "OUT", "CLASSROOM_203", t0 + 1200.0)

    # Session 2: 09:25 to 09:48 (23 min = 1380s)
    reconciler.record_transition("STU001", "IN", "CLASSROOM_203", t0 + 1500.0)
    reconciler.record_transition("STU001", "OUT", "CLASSROOM_203", t0 + 2880.0)

    decision = reconciler.evaluate_student("STU001", "P1", period_start, period_end, "CLASSROOM_203")
    assert decision.status == "PRESENT"
    assert decision.sessions_count == 2
    assert decision.total_presence_seconds == 2460.0  # 41 min
    assert abs(decision.presence_ratio - 0.82) < 1e-3

def test_partial_attendance():
    """Plan 24: IN 09:02, OUT 09:12 (10 min / 50 min = 20%) -> PARTIAL."""
    reconciler = AttendanceReconciler(present_ratio_threshold=0.75, partial_ratio_threshold=0.15)
    t0 = 300000.0
    period_start = t0
    period_end = t0 + 3000.0

    reconciler.record_transition("STU002", "IN", "CLASSROOM_203", t0 + 120.0)
    reconciler.record_transition("STU002", "OUT", "CLASSROOM_203", t0 + 720.0)  # 600s = 10 min

    decision = reconciler.evaluate_student("STU002", "P1", period_start, period_end, "CLASSROOM_203")
    assert decision.status == "PARTIAL"
    assert decision.total_presence_seconds == 600.0
    assert abs(decision.presence_ratio - 0.20) < 1e-3

def test_absent_no_entry():
    """Plan 24: No valid IN -> ABSENT."""
    reconciler = AttendanceReconciler()
    t0 = 400000.0
    period_start = t0
    period_end = t0 + 3000.0

    decision = reconciler.evaluate_student("STU003", "P1", period_start, period_end, "CLASSROOM_203")
    assert decision.status == "ABSENT"
    assert decision.total_presence_seconds == 0.0
    assert decision.presence_ratio == 0.0

def test_reconcile_period_summary():
    """Tests overall period reconciliation across a class roster."""
    reconciler = AttendanceReconciler()
    t0 = 500000.0
    period_start = t0
    period_end = t0 + 3000.0

    # STU001: full attendance (PRESENT)
    reconciler.record_transition("STU001", "IN", "CLASSROOM_203", t0 + 60.0)
    reconciler.record_transition("STU001", "OUT", "CLASSROOM_203", t0 + 2900.0)

    # STU002: brief attendance (PARTIAL)
    reconciler.record_transition("STU002", "IN", "CLASSROOM_203", t0 + 100.0)
    reconciler.record_transition("STU002", "OUT", "CLASSROOM_203", t0 + 800.0)

    # STU003: never showed up (ABSENT)

    roster = ["STU001", "STU002", "STU003"]
    summary = reconciler.reconcile_period("P1", period_start, period_end, "CLASSROOM_203", roster)

    assert summary["expected_roster_count"] == 3
    assert summary["present_count"] == 1
    assert summary["partial_count"] == 1
    assert summary["absent_count"] == 1
    assert len(summary["decisions"]) == 3
