"""Unit tests for Attendance Funnel Loss Diagnostic Engine."""
import pytest
from app.counting.loss_analyzer import FunnelLossAnalyzer, FunnelLossSummary, StudentLossClassification


def test_funnel_loss_analyzer_100_cohort():
    analyzer = FunnelLossAnalyzer()
    summary = analyzer.analyze_cohort(100)

    assert isinstance(summary, FunnelLossSummary)
    assert summary.expected == 100
    assert summary.detection_loss == 2
    assert summary.tracking_loss == 1
    assert summary.entry_event_loss == 1
    assert summary.identity_loss == 2
    assert summary.attendance_loss == 1
    assert summary.total_loss == 7
    assert summary.successful_attendance == 93
    assert summary.attendance_integrity_pct == 93.0
    assert len(summary.loss_breakdown) == 100


def test_specific_student_loss_reasons():
    analyzer = FunnelLossAnalyzer()
    
    # 1. Detection loss
    stu17 = analyzer.get_student_evidence_chain("STU017")
    assert stu17 is not None
    assert stu17.stage == "detection_loss"
    assert not stu17.detected
    assert "80px doorway threshold" in stu17.reason

    # 2. Tracking loss
    stu42 = analyzer.get_student_evidence_chain("STU042")
    assert stu42 is not None
    assert stu42.stage == "tracking_loss"
    assert stu42.detected
    assert not stu42.tracked
    assert "ByteTrack" in stu42.recommended_action

    # 3. Entry loss
    stu61 = analyzer.get_student_evidence_chain("STU061")
    assert stu61 is not None
    assert stu61.stage == "entry_event_loss"
    assert stu61.tracked
    assert not stu61.in_event

    # 4. Identity loss
    stu73 = analyzer.get_student_evidence_chain("STU073")
    assert stu73 is not None
    assert stu73.stage == "identity_loss"
    assert stu73.attendance_status == "UNCERTAIN"
    assert stu73.face_score < 0.50

    # 5. Attendance reconciliation loss
    stu95 = analyzer.get_student_evidence_chain("STU095")
    assert stu95 is not None
    assert stu95.stage == "attendance_loss"
    assert stu95.attendance_status == "PARTIAL"
    assert stu95.presence_duration_minutes < 33.75


def test_successful_student_evidence_chain():
    analyzer = FunnelLossAnalyzer()
    stu01 = analyzer.get_student_evidence_chain("STU001")
    assert stu01 is not None
    assert stu01.stage == "success"
    assert stu01.detected
    assert stu01.tracked
    assert stu01.capture_zone_entered
    assert stu01.best_frame_selected
    assert stu01.face_score > 0.80
    assert stu01.body_score > 0.80
    assert stu01.fusion_score > 0.80
    assert stu01.in_event
    assert stu01.presence_duration_minutes > 35.0
    assert stu01.attendance_status == "PRESENT"


def test_funnel_summary_dict_serialization():
    analyzer = FunnelLossAnalyzer()
    summary = analyzer.analyze_cohort(100)
    data = summary.to_dict()
    assert data["expected"] == 100
    assert data["losses"]["total_loss"] == 7
    assert data["attendance_integrity_pct"] == 93.0
    assert len(data["loss_breakdown"]) == 100
