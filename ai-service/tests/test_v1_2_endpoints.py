"""Tests for V1.2 System Health, Loss Analysis, and Camera Survey REST endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.backend.api import app

client = TestClient(app)


def test_health_check_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UP"
    assert data["service"] == "ai-service"
    assert data["version"] == "1.2.0"
    assert "timestamp_iso" in data


def test_system_status_endpoint():
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("HEALTHY", "DEGRADED")
    assert data["database"]["connected"] is True
    assert data["database"]["engine"] == "sqlite"
    assert data["cameras"]["total"] == 10
    assert data["system_resources"]["ram_mb"] > 0
    assert "cpu_percent" in data["system_resources"]


def test_loss_analysis_endpoint():
    res = client.get("/api/campus/loss_analysis?cohort_size=100")
    assert res.status_code == 200
    data = res.json()
    assert data["expected"] == 100
    assert data["losses"]["total_loss"] == 7
    assert data["losses"]["detection_loss"] == 2
    assert data["losses"]["tracking_loss"] == 1
    assert data["losses"]["entry_event_loss"] == 1
    assert data["losses"]["identity_loss"] == 2
    assert data["losses"]["attendance_loss"] == 1
    assert data["attendance_integrity_pct"] == 93.0
    assert len(data["loss_breakdown"]) == 100


def test_student_evidence_chain_endpoint():
    # STU017 (Detection loss)
    res = client.get("/api/students/STU017/evidence_chain")
    assert res.status_code == 200
    stu17 = res.json()
    assert stu17["student_id"] == "STU017"
    assert stu17["stage"] == "detection_loss"
    assert not stu17["detected"]

    # STU001 (Successful student)
    res_good = client.get("/api/students/STU001/evidence_chain")
    assert res_good.status_code == 200
    stu1 = res_good.json()
    assert stu1["student_id"] == "STU001"
    assert stu1["stage"] == "success"
    assert stu1["attendance_status"] == "PRESENT"
    assert stu1["fusion_score"] >= 0.80

    # Non-existent student
    res_bad = client.get("/api/students/STU9999/evidence_chain")
    assert res_bad.status_code == 404


def test_cameras_survey_endpoints():
    # All cameras
    res = client.get("/api/cameras/survey")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cameras"] == 10
    assert data["all_production_ready"] is True
    assert data["average_calibration_score_pct"] >= 95.0

    # Single camera
    res_single = client.get("/api/cameras/CAM-101-ENTRY/survey")
    assert res_single.status_code == 200
    cam_data = res_single.json()
    assert cam_data["profile"]["camera_id"] == "CAM-101-ENTRY"
    assert cam_data["profile"]["avg_face_width_px"] >= 80
    assert cam_data["validation"]["is_production_ready"] is True
    assert cam_data["validation"]["face_resolution_ok"] is True

    # Bad camera
    res_bad = client.get("/api/cameras/CAM-NONEXISTENT/survey")
    assert res_bad.status_code == 404
