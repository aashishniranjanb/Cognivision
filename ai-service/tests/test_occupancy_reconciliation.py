"""Tests for OccupancyCounter and OccupancyReconciler."""
import pytest
from app.counting.occupancy_counter import OccupancyCounter
from app.counting.occupancy_reconciler import OccupancyReconciler
from app.counting.count_metrics import compute_campus_kpis

def test_occupancy_counter_events():
    oc = OccupancyCounter(classroom_id="CLASSROOM_101", baseline_occupancy=0)
    oc.record_event("IN", count=50)
    oc.record_event("OUT", count=11)
    
    assert oc.event_occupancy == 39
    
    oc.update_vision_count(40)
    snap = oc.get_occupancy_snapshot()
    assert snap["vision_count"] == 40
    assert snap["event_occupancy"] == 39
    assert snap["difference"] == 1

def test_occupancy_reconciliation_categories():
    reconciler = OccupancyReconciler(tolerance=1)
    
    # 1. Perfect match
    r1 = reconciler.reconcile(
        classroom_id="C101",
        vision_count=42,
        event_occupancy=42,
        identified_count=40,
        unknown_count=2
    )
    assert r1.status == "PERFECT_MATCH"
    assert r1.difference == 0
    assert r1.unidentified_present == 2
    
    # 2. Minor mismatch within tolerance
    r2 = reconciler.reconcile(
        classroom_id="C101",
        vision_count=42,
        event_occupancy=41,
        identified_count=40,
        unknown_count=1,
        uncertain_count=1
    )
    assert r2.status == "MINOR_MISMATCH"
    assert r2.difference == 1
    
    # 3. Severe occupancy mismatch
    r3 = reconciler.reconcile(
        classroom_id="C101",
        vision_count=42,
        event_occupancy=47,
        identified_count=38,
        unknown_count=4
    )
    assert r3.status == "OCCUPANCY_MISMATCH"
    assert r3.difference == 5

def test_campus_kpi_computation():
    kpis = compute_campus_kpis(
        expected_students=100,
        physical_detected=98,
        active_tracks=97,
        successfully_identified=94,
        unknown_count=2,
        uncertain_count=1,
        current_occupancy=96
    )
    assert kpis.capture_success_rate == 0.98
    assert kpis.tracking_success_rate == round(97 / 98, 4)
    assert kpis.identity_success_rate == round(94 / 97, 4)
    assert kpis.overall_pipeline_success == 0.94
