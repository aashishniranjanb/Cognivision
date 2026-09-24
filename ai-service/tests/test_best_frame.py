"""Tests for TrackCaptureBuffer and BestFrameSelector."""
import pytest
import numpy as np
import cv2
from app.face.best_frame import TrackCaptureBuffer, BestFrameSelector

def test_best_frame_selection():
    buffer = TrackCaptureBuffer(max_candidates=5)
    
    # 1. Blurry small face
    blurry = np.full((30, 30, 3), 120, dtype=np.uint8)
    c1 = buffer.add_candidate(blurry, bbox=(10, 10, 40, 40))
    
    # 2. Medium face with texture
    medium = np.random.randint(50, 200, (60, 60, 3), dtype=np.uint8)
    c2 = buffer.add_candidate(medium, bbox=(10, 10, 70, 70))
    
    # 3. High-contrast sharp face with prominent width (90px)
    sharp = np.zeros((90, 90, 3), dtype=np.uint8)
    cv2.rectangle(sharp, (10, 10), (80, 80), (255, 255, 255), 2)
    cv2.circle(sharp, (45, 45), 20, (200, 200, 200), -1)
    c3 = buffer.add_candidate(sharp, bbox=(10, 10, 100, 100))
    
    best = buffer.get_best_candidate()
    assert best is not None
    assert best.composite_score == c3.composite_score
    assert best.composite_score > c1.composite_score

def test_ring_buffer_bounded():
    buffer = TrackCaptureBuffer(max_candidates=3)
    crop = np.full((50, 50, 3), 120, dtype=np.uint8)
    
    for i in range(10):
        buffer.add_candidate(crop, bbox=(0, 0, 50, 50))
    
    assert buffer.size() == 3

def test_best_frame_selector_multi_track():
    selector = BestFrameSelector(max_buffer_per_track=5)
    
    crop1 = np.full((40, 40, 3), 100, dtype=np.uint8)
    crop2 = np.full((80, 80, 3), 120, dtype=np.uint8)
    cv2.line(crop2, (0, 0), (80, 80), (255, 255, 255), 3)
    
    selector.add_track_observation(17, crop1, bbox=(10, 10, 50, 50))
    selector.add_track_observation(17, crop2, bbox=(10, 10, 90, 90))
    
    best17 = selector.select_best(17)
    assert best17 is not None
    assert best17.size_score > 0.5
    
    # Unknown track returns None
    assert selector.select_best(999) is None
    
    # Clear track
    selector.clear_track(17)
    assert selector.select_best(17) is None
