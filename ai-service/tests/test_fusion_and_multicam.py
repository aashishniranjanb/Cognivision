"""Unit tests verifying Adaptive Fusion weighting, Body Re-ID matching, and Multi-Camera Reconciliation."""
import time
from app.fusion.observation import ModalityObservation
from app.fusion.adaptive_fusion import AdaptiveFusionEngine
from app.attendance.event import AttendanceEvent
from app.multicam.coordinator import MultiCameraCoordinator

def test_adaptive_fusion_face_dominance():
    engine = AdaptiveFusionEngine(acceptance_threshold=0.50)
    
    # Case: High Face Reliability (0.90), Moderate Body Reliability (0.75)
    obs = [
        ModalityObservation(modality="face", candidate_id="STU001", identity_score=0.92, reliability=0.90, track_id=1, timestamp=time.time()),
        ModalityObservation(modality="body", candidate_id="STU001", identity_score=0.84, reliability=0.75, track_id=1, timestamp=time.time())
    ]
    fused = engine.fuse(track_id=1, observations=obs)
    assert fused.decision == "STU001"
    # Face weight should exceed Body weight because B_face=1.0*0.9 > B_body=0.85*0.75
    assert fused.modality_weights["face"] > fused.modality_weights["body"]

def test_adaptive_fusion_occluded_face_body_fallback():
    engine = AdaptiveFusionEngine(acceptance_threshold=0.50)
    
    # Case: Occluded face (reliability=0.25), Clean Body (reliability=0.85)
    obs = [
        ModalityObservation(modality="face", candidate_id="STU002", identity_score=0.80, reliability=0.25, track_id=2, timestamp=time.time()),
        ModalityObservation(modality="body", candidate_id="STU001", identity_score=0.88, reliability=0.85, track_id=2, timestamp=time.time())
    ]
    fused = engine.fuse(track_id=2, observations=obs)
    # Body should dominate and elect STU001 despite face seeing STU002 with low reliability
    assert fused.modality_weights["body"] > fused.modality_weights["face"]
    assert fused.decision == "STU001"

def test_multicamera_event_reconciliation():
    coord = MultiCameraCoordinator()
    t0 = 1000.0

    # Camera 1 (ENTRY_CAM_01 / Track 17) sees STU001 enter
    evt_in = AttendanceEvent(
        event_id="EVT-01",
        student_id="STU001",
        camera_id="ENTRY_CAM_01",
        location_id="CLASSROOM_203",
        direction="IN",
        timestamp=t0,
        timestamp_iso="2026-09-20T10:00:00",
        track_id=17,
        confidence=0.89
    )
    s1 = coord.handle_event(evt_in)
    assert s1.status == "INSIDE"
    assert s1.last_camera == "ENTRY_CAM_01"

    # Camera 2 (EXIT_CAM_01 / Track 04) sees STU001 exit 40 minutes later
    t1 = t0 + 2400.0
    evt_out = AttendanceEvent(
        event_id="EVT-02",
        student_id="STU001",
        camera_id="EXIT_CAM_01",
        location_id="CLASSROOM_203",
        direction="OUT",
        timestamp=t1,
        timestamp_iso="2026-09-20T10:40:00",
        track_id=4,
        confidence=0.85
    )
    s2 = coord.handle_event(evt_out)
    assert s2.status == "EXITED"
    assert s2.last_camera == "EXIT_CAM_01"
    assert s2.total_time_inside == 2400.0
