"""Tests for CameraQualityAnalyzer evaluating sharpness, lighting, face pixel sizes, and ratings."""
import pytest
import numpy as np
import cv2
from app.camera.camera_quality import CameraQualityAnalyzer

def test_camera_quality_sharp_frame():
    analyzer = CameraQualityAnalyzer(camera_id="C203_ENTRY")
    
    # Generate sharp synthetic frame with high contrast edges
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.rectangle(frame, (100, 100), (400, 400), (255, 255, 255), -1)
    cv2.circle(frame, (800, 400), 100, (128, 128, 128), -1)
    
    # Simulated face of 60px width
    face_boxes = [(500, 200, 560, 260)]
    
    rep = analyzer.assess_frame(frame, fps=25.0, face_bboxes=face_boxes)
    assert rep.width == 1280
    assert rep.height == 720
    assert rep.fps == 25.0
    assert rep.average_face_width_px == 60.0
    assert rep.blur_score > 80.0
    assert rep.capture_quality in ["GOOD", "MARGINAL"]

def test_camera_quality_blurry_or_dark():
    analyzer = CameraQualityAnalyzer(camera_id="C203_ENTRY")
    
    # Generate completely dark frame
    dark_frame = np.full((720, 1280, 3), 10, dtype=np.uint8)
    rep_dark = analyzer.assess_frame(dark_frame, fps=25.0, face_bboxes=[])
    assert rep_dark.capture_quality == "POOR"
    
    # Generate blurry frame with small face (< 20px)
    smooth_frame = np.full((720, 1280, 3), 120, dtype=np.uint8)
    small_face = [(100, 100, 115, 115)] # 15px width
    rep_blurry = analyzer.assess_frame(smooth_frame, fps=25.0, face_bboxes=small_face)
    assert rep_blurry.capture_quality == "POOR"
    assert rep_blurry.average_face_width_px == 15.0
