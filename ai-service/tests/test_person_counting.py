"""Tests for PersonCounter verifying track continuity, noise suppression, and physical counting."""
import pytest
from app.counting.person_counter import PersonCounter, TrackState

def test_single_person_persistent_count():
    pc = PersonCounter(min_confirm_frames=3)
    
    # Frame 1: Tentative
    pc.update([101])
    assert pc.current_physical_count == 0
    assert pc.active_track_count == 1
    
    # Frame 2: Still tentative
    pc.update([101])
    assert pc.current_physical_count == 0
    
    # Frame 3: Confirmed
    pc.update([101])
    assert pc.current_physical_count == 1
    
    # Same person across 100 frames remains 1 person
    for _ in range(100):
        pc.update([101])
    assert pc.current_physical_count == 1

def test_transient_noise_filtered():
    pc = PersonCounter(min_confirm_frames=3, max_lost_frames=2)
    
    # Frame 1: Glitch detection (e.g. shadow or glare)
    pc.update([999])
    assert pc.current_physical_count == 0
    
    # Frame 2 & 3: Glitch disappears
    pc.update([])
    pc.update([])
    pc.update([])
    
    # Track 999 should be pruned as lost
    assert 999 not in pc.tracks
    assert pc.current_physical_count == 0

def test_two_people_crossing():
    pc = PersonCounter(min_confirm_frames=2)
    
    # Person 101 and Person 102 appear
    pc.update([101, 102])
    pc.update([101, 102])
    assert pc.current_physical_count == 2
    
    # Crossing: both present
    for _ in range(10):
        pc.update([101, 102])
    assert pc.current_physical_count == 2
    
    # Person 102 exits, 101 remains
    for _ in range(5):
        pc.update([101])
    assert 101 in pc.confirmed_track_ids

def test_directional_crossings_and_net_occupancy():
    pc = PersonCounter(min_confirm_frames=1)
    
    pc.update([10, 20, 30])
    pc.record_crossing(10, "IN")
    pc.record_crossing(20, "IN")
    pc.record_crossing(30, "IN")
    
    summary = pc.get_summary()
    assert summary["total_entered"] == 3
    assert summary["total_exited"] == 0
    assert summary["net_occupancy_change"] == 3
    
    # Person 10 leaves
    pc.record_crossing(10, "OUT")
    summary = pc.get_summary()
    assert summary["total_exited"] == 1
    assert summary["net_occupancy_change"] == 2
