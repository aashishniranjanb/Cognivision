"""Tests for Step 8 — Phase-II Realistic Scale and Attendance Integrity (Plan 24)."""
import pytest
from benchmarks.benchmark_phase2_realistic import (
    run_scale_step,
    benchmark_phase2_progression,
    benchmark_attendance_integrity
)

def test_scale_step_execution():
    res100 = run_scale_step(students=100, cameras=2, tracks=70, iterations=10)
    assert res100.students == 100
    assert res100.cameras == 2
    assert res100.active_tracks == 70
    assert res100.fps_per_camera >= 15.0
    assert res100.dropped_frames == 0
    assert res100.false_accepts == 0
    assert res100.detection_latency_ms < 5.0

    res500 = run_scale_step(students=500, cameras=10, tracks=350, iterations=10)
    assert res500.students == 500
    assert res500.cameras == 10
    assert res500.active_tracks == 350
    assert res500.dropped_frames == 0
    assert res500.false_accepts == 0

def test_attendance_integrity_funnel():
    report = benchmark_attendance_integrity(100)
    assert report.expected_students == 100
    assert report.detected == 98
    assert report.tracked == 97
    assert report.entered == 96
    assert report.identified == 94
    assert report.correct_attendance == 93
    assert report.unknown == 1
    assert report.uncertain == 1
    assert report.missed == 2
    assert report.false_attendance == 0
    assert report.capture_success_rate == 0.98
    assert report.false_acceptance_rate == 0.0

def test_phase2_progression():
    steps = benchmark_phase2_progression(max_scale=500)
    assert len(steps) == 5
    scales = [s.students for s in steps]
    assert scales == [100, 200, 300, 400, 500]
    cameras = [s.cameras for s in steps]
    assert cameras == [2, 4, 6, 8, 10]

def test_scale_step_600_plus():
    res600 = run_scale_step(students=600, cameras=12, tracks=420, iterations=10)
    assert res600.students == 600
    assert res600.cameras == 12
    assert res600.active_tracks == 420
    assert res600.fps_per_camera >= 18.0
    assert res600.dropped_frames == 0
    assert res600.false_accepts == 0
    assert res600.ram_mb < 800.0

    res800 = run_scale_step(students=800, cameras=16, tracks=560, iterations=10)
    assert res800.students == 800
    assert res800.cameras == 16
    assert res800.active_tracks == 560
    assert res800.fps_per_camera >= 15.0
    assert res800.dropped_frames == 0
    assert res800.false_accepts == 0

def test_phase2_progression_600_plus():
    steps = benchmark_phase2_progression(max_scale=800)
    assert len(steps) == 8
    scales = [s.students for s in steps]
    assert scales == [100, 200, 300, 400, 500, 600, 700, 800]
    assert steps[-1].students == 800
