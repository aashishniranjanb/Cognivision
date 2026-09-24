"""Unit tests for Real CCTV Camera Survey & Corridor Calibration Engine."""
import pytest
from app.camera.camera_survey import CameraSurveyEngine, CameraSurveyProfile, SurveyValidationResult


def test_campus_default_surveys():
    engine = CameraSurveyEngine()
    campus_result = engine.validate_all_campus_cameras()

    assert campus_result["total_cameras"] == 10
    assert campus_result["all_production_ready"] is True
    assert campus_result["average_calibration_score_pct"] >= 95.0
    assert "CAM-101-ENTRY" in campus_result["cameras"]
    assert "CAM-203-ENTRY" in campus_result["cameras"]


def test_camera_survey_face_size_threshold():
    engine = CameraSurveyEngine()

    # Profile with face width too small (50px < 80px threshold)
    bad_profile = CameraSurveyProfile(
        camera_id="CAM-TEST-SMALL-FACE",
        classroom_id="C999",
        resolution_width=1280,
        resolution_height=720,
        fps=20.0,
        mount_height_m=3.8,  # too high
        door_distance_m=5.5,  # too far
        lens_focal_length_mm=2.8,
        horizontal_angle_deg=25.0,
        vertical_angle_deg=35.0,
        avg_person_height_px=220,
        avg_face_width_px=45,  # FAIL (< 80px)
        illumination_lux=30.0,  # FAIL (< 50 lux)
        laplacian_sharpness=75.0,  # FAIL (< 100)
        rtsp_latency_ms=180.0,  # FAIL (> 120ms)
        corridor_width_m=2.5,
        is_corridor_controlled=False,
        blind_spot_coverage_pct=72.0,
    )

    res = engine.survey_camera(bad_profile)
    assert not res.is_production_ready
    assert not res.face_resolution_ok
    assert not res.illumination_ok
    assert not res.sharpness_ok
    assert not res.latency_ok
    assert not res.geometry_ok
    assert len(res.warnings) >= 4
    assert len(res.recommendations) >= 4
    assert res.score_pct < 50.0


def test_camera_survey_optimal_corridor():
    engine = CameraSurveyEngine()
    good_profile = CameraSurveyProfile(
        camera_id="CAM-TEST-GOOD",
        classroom_id="C101",
        resolution_width=1920,
        resolution_height=1080,
        fps=30.0,
        mount_height_m=2.6,
        door_distance_m=2.5,
        lens_focal_length_mm=4.0,
        horizontal_angle_deg=5.0,
        vertical_angle_deg=15.0,
        avg_person_height_px=580,
        avg_face_width_px=110,
        illumination_lux=180.0,
        laplacian_sharpness=160.0,
        rtsp_latency_ms=35.0,
        corridor_width_m=1.1,
        is_corridor_controlled=True,
        blind_spot_coverage_pct=99.0,
    )

    res = engine.survey_camera(good_profile)
    assert res.is_production_ready
    assert res.face_resolution_ok
    assert res.illumination_ok
    assert res.sharpness_ok
    assert res.latency_ok
    assert res.geometry_ok
    assert res.score_pct == 100.0
    assert len(res.warnings) == 0
