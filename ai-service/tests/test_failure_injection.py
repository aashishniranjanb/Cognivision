"""Phase 14 Failure Injection Suite: Deliberately breaking camera, faces, and timestamps."""
import pytest
import time
from app.events.event_schema import CampusEvent
from app.events.event_reconciler import EventReconciler
from app.camera.stream_config import CameraStreamConfig, CameraConnectionState
from app.camera.health_monitor import CameraHealthMonitor
from app.camera.reconnect import ReconnectPolicy
from app.fusion.adaptive_fusion import AdaptiveFusionEngine
from app.fusion.observation import ModalityObservation
from app.identity.robust_identity import RobustIdentityManager

def test_failure_1_camera_disconnect_and_system_survives():
    """Test 1: One camera disconnects -> marked DEGRADED, others unaffected."""
    monitor = CameraHealthMonitor()
    monitor.update_metrics("CAM_1", CameraConnectionState.STREAMING, 25.0, 0, 1, 15.0, 0)
    monitor.update_metrics("CAM_2", CameraConnectionState.STREAMING, 25.0, 0, 1, 16.0, 0)

    # Inject failure on CAM_1
    monitor.update_metrics("CAM_1", CameraConnectionState.DEGRADED, 0.0, 10, 0, 0.0, 1, error="RTSP Socket Timeout")

    cam1 = monitor.get_health("CAM_1")
    cam2 = monitor.get_health("CAM_2")

    assert cam1.state == CameraConnectionState.DEGRADED
    assert cam2.state == CameraConnectionState.STREAMING # Untouched

def test_failure_2_temporary_face_loss_memory_decay():
    """Test 2: Face disappears for 3-5s -> track survives and retains identity via memory decay."""
    mgr = RobustIdentityManager(confirm_threshold=0.50, min_confirmed_hits=2, memory_decay_frames=15)
    # Establish confirmed identity
    for _ in range(3):
        mgr.update_observation(track_id=10, candidate_id="STU001", similarity=0.90, reliability=0.90)

    # Face lost for 5 frames
    for _ in range(5):
        status, conf_id, score = mgr.update_observation(track_id=10, candidate_id=None, similarity=0.0, reliability=0.0)
        assert status == "CONFIRMED"
        assert conf_id == "STU001" # Identity preserved through occlusion memory

def test_failure_3_unknown_person_rejection():
    """Test 3: Unregistered person enters -> rejected as UNKNOWN, zero student attendance."""
    fusion = AdaptiveFusionEngine(acceptance_threshold=0.50)
    obs = [
        ModalityObservation("face", "STU001", identity_score=0.25, reliability=0.70, track_id=88, timestamp=time.time()),
        ModalityObservation("body", "STU002", identity_score=0.20, reliability=0.60, track_id=88, timestamp=time.time())
    ]
    decision = fusion.fuse(track_id=88, observations=obs)
    assert decision.decision is None or decision.decision == "UNKNOWN"

def test_failure_4_rapid_flap_suppression():
    """Test 4: ENTRY -> EXIT -> ENTRY within <2.0s -> reconciler drops contradictory event."""
    reconciler = EventReconciler(min_event_interval_sec=2.0)
    now = time.time()
    e1 = CampusEvent.create_attendance("STU001", "C1", "ROOM_101", 1, "IN", 0.95, timestamp=now)
    e2 = CampusEvent.create_attendance("STU001", "C2", "ROOM_101", 1, "OUT", 0.95, timestamp=now + 0.5)

    res1 = reconciler.reconcile(e1)
    res2 = reconciler.reconcile(e2)
    assert res1.action == "ACCEPTED"
    assert res2.is_conflict
    assert res2.action == "DROPPED_CONTRADICTORY"

def test_failure_5_face_body_disagreement():
    """Test 5: Face matches STU001 while body matches STU004 -> fusion evaluates uncertainty."""
    fusion = AdaptiveFusionEngine(acceptance_threshold=0.55)
    # Balanced moderate confidences with opposing identities
    obs = [
        ModalityObservation("face", "STU001", identity_score=0.52, reliability=0.50, track_id=7, timestamp=time.time()),
        ModalityObservation("body", "STU004", identity_score=0.53, reliability=0.50, track_id=7, timestamp=time.time())
    ]
    decision = fusion.fuse(track_id=7, observations=obs)
    # With competing identities splitting weight, neither should cross strong threshold cleanly
    assert decision.decision is None or decision.decision == "UNCERTAIN" or decision.fused_score < 0.55

