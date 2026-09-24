"""Tests for Phase-II Full Multi-Classroom Live Rehearsal Runner."""
import pytest
from benchmarks.phase2_live_rehearsal import run_full_phase2_rehearsal, RehearsalSummary


def test_phase2_live_rehearsal_execution():
    summary = run_full_phase2_rehearsal(enrolled_count=100, classrooms=["C101", "C203"])
    assert isinstance(summary, RehearsalSummary)
    assert summary.enrolled_students == 100
    assert summary.classrooms_count == 2
    assert summary.cameras_count == 4
    assert summary.total_events_processed > 80
    assert summary.attendance_confirmed > 70
    assert summary.unknown_rejected > 0
    assert summary.exceptions_raised > 0
    assert summary.false_acceptance_rate_pct == 0.0
    assert summary.rehearsal_duration_sec > 0.0
