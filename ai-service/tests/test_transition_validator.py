"""Tests for TransitionValidator spatio-temporal validation."""
import pytest
from app.attendance.transition_validator import TransitionValidator

def test_valid_entry_and_exit():
    tv = TransitionValidator(min_transit_seconds=4.0, flap_window_seconds=2.0)
    
    # 1. Enters room 101
    r1 = tv.validate_transition("STU001", "IN", "CLASSROOM_101", timestamp=100.0)
    assert r1.is_valid is True
    assert r1.action == "ACCEPTED"
    assert r1.current_state == "INSIDE"
    assert r1.current_location == "CLASSROOM_101"
    
    # 2. Exits room 101 after 100 seconds
    r2 = tv.validate_transition("STU001", "OUT", "CLASSROOM_101", timestamp=200.0)
    assert r2.is_valid is True
    assert r2.action == "ACCEPTED"
    assert r2.current_state == "OUTSIDE"
    assert r2.current_location == "OUTSIDE"

def test_duplicate_events_suppressed():
    tv = TransitionValidator()
    
    # First IN
    tv.validate_transition("STU002", "IN", "CLASSROOM_101", timestamp=100.0)
    
    # Repeated IN while already inside
    r_dup = tv.validate_transition("STU002", "IN", "CLASSROOM_101", timestamp=115.0)
    assert r_dup.is_valid is False
    assert r_dup.action == "SUPPRESSED_DUPLICATE"

def test_rapid_flap_suppressed():
    tv = TransitionValidator(flap_window_seconds=2.0)
    
    # IN at t=100.0
    tv.validate_transition("STU003", "IN", "CLASSROOM_101", timestamp=100.0)
    
    # Rapid OUT at t=101.0 (< 2.0s)
    r_flap = tv.validate_transition("STU003", "OUT", "CLASSROOM_101", timestamp=101.0)
    assert r_flap.is_valid is False
    assert r_flap.action == "SUPPRESSED_DUPLICATE"

def test_teleportation_anomaly_detection():
    tv = TransitionValidator(min_transit_seconds=5.0)
    
    # In room 101 at 10:00:00
    tv.validate_transition("STU004", "IN", "CLASSROOM_101", timestamp=1000.0)
    
    # Impossible jump to room 203 in 1.5 seconds (< 5.0s)
    r_jump = tv.validate_transition("STU004", "IN", "CLASSROOM_203", timestamp=1001.5)
    assert r_jump.is_valid is False
    assert r_jump.action == "LOCATION_TRANSITION_ANOMALY"

def test_valid_classroom_transfer_auto_reconciled():
    tv = TransitionValidator(min_transit_seconds=5.0)
    
    # In room 101 at 10:00:00
    tv.validate_transition("STU005", "IN", "CLASSROOM_101", timestamp=1000.0)
    
    # Moves to room 203 after 25 seconds (plausible walking transit)
    r_move = tv.validate_transition("STU005", "IN", "CLASSROOM_203", timestamp=1025.0)
    assert r_move.is_valid is True
    assert r_move.action == "AUTO_RECONCILED"
    assert r_move.current_location == "CLASSROOM_203"
