"""Unit tests for Period Attendance CSV Export and Evidence endpoint."""
import pytest
import csv
import io
from app.backend.report_service import ReportService
from app.backend.attendance_repository import AttendanceRepository
from app.events.event_schema import CampusEvent
from app.state.global_student_state import GlobalStudentStateManager
from fastapi.testclient import TestClient
from app.backend.api import app, campus_manager

def test_export_daily_csv_content(tmp_path):
    db_file = tmp_path / "test_csv.db"
    audit_file = tmp_path / "audit.jsonl"
    repo = AttendanceRepository(db_path=str(db_file), audit_file=str(audit_file))
    state_mgr = GlobalStudentStateManager()

    report_svc = ReportService(attendance_repo=repo, state_mgr=state_mgr)

    # Export CSV as string
    csv_text = report_svc.export_daily_csv(date_str="2026-09-21", classroom_id="CLASSROOM_203")
    assert "Date,Student ID,Student Name" in csv_text
    assert "CLASSROOM_203" in csv_text
    assert "STU001" in csv_text
    assert "VLSI Design & Embedded Systems" in csv_text

    # Verify CSV is parseable by standard csv reader
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) >= 4  # 4 periods for at least 1 student
    assert rows[0]["Period ID"] == "P1"
    assert rows[0]["Attendance Status"] in ["PRESENT", "PARTIAL", "ABSENT", "UNCERTAIN"]

def test_export_daily_csv_file_output(tmp_path):
    repo = AttendanceRepository(db_path=str(tmp_path / "test.db"), audit_file=str(tmp_path / "a.jsonl"))
    report_svc = ReportService(attendance_repo=repo)
    out_file = tmp_path / "reports" / "daily_test.csv"

    csv_text = report_svc.export_daily_csv(output_path=str(out_file))
    assert out_file.exists()
    assert len(out_file.read_text(encoding="utf-8")) > 50

def test_api_csv_and_evidence_endpoints():
    client = TestClient(app)

    # 1. Camera Health Endpoint
    resp_health = client.get("/api/camera/health")
    assert resp_health.status_code == 200
    health_data = resp_health.json()
    assert isinstance(health_data, dict)

    # 2. CSV Export Endpoint
    resp_csv = client.get("/api/reports/export/csv?classroom_id=CLASSROOM_203")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "attendance_report" in resp_csv.headers["content-disposition"]
    assert "Student ID" in resp_csv.text

    # 3. Evidence Audit Endpoint
    resp_ev = client.get("/api/evidence/STU001")
    assert resp_ev.status_code == 200
    ev_data = resp_ev.json()
    assert ev_data["student_id"] == "STU001"
    assert "biometric_evidence" in ev_data
    assert "spatio_temporal_audit" in ev_data
    assert "periods" in ev_data
    assert ev_data["biometric_evidence"]["fused_decision"] in ["CONFIRMED", "PROVISIONAL"]
