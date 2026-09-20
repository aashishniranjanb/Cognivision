"""Comprehensive Suite Testing Week 3 Day 3 Scenarios: Temporary Occlusion, Anomaly Logging, and Period Evaluation."""
import time
from datetime import datetime
from app.identity.robust_identity import RobustIdentityManager
from app.schedule.schedule_manager import ScheduleManager
from app.attendance.comprehensive_engine import ComprehensiveAttendanceEngine

def test_temporary_face_disappearance():
    mgr = RobustIdentityManager(confirm_threshold=0.50, min_confirmed_hits=2, memory_decay_frames=5)
    
    # 2 good hits confirm identity
    s1, id1, c1 = mgr.update_observation(17, "STU001", similarity=0.85, reliability=0.90)
    s2, id2, c2 = mgr.update_observation(17, "STU001", similarity=0.88, reliability=0.92)
    assert s2 == "CONFIRMED"
    assert id2 == "STU001"

    # Face temporarily disappears for 3 frames (occlusion) -> Identity must NOT be replaced with UNKNOWN
    for _ in range(3):
        s_occ, id_occ, _ = mgr.update_observation(17, candidate_id=None, similarity=0.0, reliability=0.0)
        assert s_occ == "CONFIRMED"
        assert id_occ == "STU001"

    # Face returns -> Confirmation remains continuous
    s_ret, id_ret, _ = mgr.update_observation(17, "STU001", similarity=0.86, reliability=0.90)
    assert s_ret == "CONFIRMED"
    assert id_ret == "STU001"

def test_anomaly_logging():
    mgr = RobustIdentityManager(confirm_threshold=0.50)
    # Low quality face trigger
    mgr.update_observation(18, "STU002", similarity=0.80, reliability=0.30)
    assert any(a.anomaly_type == "LOW_FACE_QUALITY" for a in mgr.anomalies)

    # Unknown person trigger
    mgr.update_observation(19, "STU999", similarity=0.15, reliability=0.85)
    assert any(a.anomaly_type == "UNKNOWN_PERSON" for a in mgr.anomalies)

def test_period_schedule_matching():
    sm = ScheduleManager()
    p = sm.get_active_period("CLASSROOM_203", datetime(2026, 9, 20, 9, 15))
    assert p is not None
    assert p.period_id == "P1"
    assert p.subject == "VLSI Design"
