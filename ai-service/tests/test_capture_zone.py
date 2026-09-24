"""Tests for CaptureZone evaluation of geometric funnels and crossing lines."""
import pytest
from app.camera.capture_zone import CaptureZone

def test_point_and_bbox_in_capture_zone():
    zone = CaptureZone(
        zone_polygon=[(100, 100), (500, 100), (500, 500), (100, 500)],
        crossing_line=((100, 300), (500, 300))
    )
    
    # Point inside
    assert zone.is_point_in_zone((300, 300)) is True
    # Point outside
    assert zone.is_point_in_zone((50, 50)) is False
    
    # BBox inside
    bbox_in = (200, 200, 260, 280)
    assert zone.is_bbox_in_zone(bbox_in) is True
    
    # BBox outside
    bbox_out = (600, 600, 650, 680)
    assert zone.is_bbox_in_zone(bbox_out) is False

def test_crossing_line_evaluation():
    zone = CaptureZone(crossing_line=((0, 250), (600, 250)))
    
    # Crossing from top (y=200) to bottom (y=300) -> IN
    assert zone.evaluate_crossing(prev_y=200, curr_y=300) == "IN"
    
    # Crossing from bottom (y=300) to top (y=200) -> OUT
    assert zone.evaluate_crossing(prev_y=300, curr_y=200) == "OUT"
    
    # Moving entirely on one side -> None
    assert zone.evaluate_crossing(prev_y=100, curr_y=150) is None
