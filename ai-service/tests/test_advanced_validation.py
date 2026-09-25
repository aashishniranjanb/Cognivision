"""
Sprint F Advanced Real-World Validation Suite (Tasks 36-40):
- Task 36: Pose Diversity Test (Multi-angle profile & tilt recovery)
- Task 37: Occlusion Recovery Test (Masks, glasses, partial occlusions)
- Task 38: Similar Faces Separation Test (Twin/lookalike margin separation)
- Task 39: Unknown Visitors Audit Test (Stranger isolation vs degraded frame)
- Task 40: Cross-Camera Identity Consistency Test (Spatial-temporal handover)
"""

import time
import pytest
import numpy as np
import cv2

from app.face.index_manager import FaissIndexManager
from app.face.candidate_retriever import FaissCandidateRetriever
from app.face.candidate_verifier import CandidateVerifier
from app.face.unknown_rejector import UnknownPersonClassifier
from app.identity.identity_memory import IdentityMemoryManager


class MockRepo:
    def __init__(self, students_dict):
        self.students = students_dict

    def get_template_embedding(self, student_id: str):
        if student_id in self.students:
            return self.students[student_id]["canonical"].tolist()
        return None

    def get_variant_embeddings(self, student_id: str):
        if student_id in self.students:
            return self.students[student_id]["variants"]
        return []


# ============================================================================
# Task 36: Pose Diversity Test (Extreme profiles & tilt recovery)
# ============================================================================
def test_pose_diversity_and_angle_adaptation():
    """Verifies that non-frontal queries (yaw ±25° to ±35°, pitch ±15°) successfully
    match against the enrolled variant cluster even when frontal similarity is lower."""
    rng = np.random.RandomState(42)
    manager = FaissIndexManager(dim=512)

    # Base frontal vector for STU_POSE_01
    canonical = rng.randn(512).astype(np.float32)
    canonical /= np.linalg.norm(canonical)

    # Create distinct pose variants
    poses = ["FRONTAL", "LEFT_PROFILE", "RIGHT_PROFILE", "TILT_UP", "TILT_DOWN"]
    variants = []
    variant_vectors = {}

    for idx, p in enumerate(poses):
        noise = rng.randn(512).astype(np.float32)
        noise /= np.linalg.norm(noise)
        # Cosine similarity ~ 0.88 with canonical
        v_vec = (0.88 * canonical + 0.12 * noise).astype(np.float32)
        v_vec /= np.linalg.norm(v_vec)
        variants.append((idx + 1, v_vec.tolist(), p, 0.92))
        variant_vectors[p] = v_vec
        manager.add_vector("STU_POSE_01", v_vec, pose=p)

    # Add 20 distractor students into index
    for i in range(20):
        dist_base = rng.randn(512).astype(np.float32)
        dist_base /= np.linalg.norm(dist_base)
        manager.add_vector(f"DISTRACTOR_{i:02d}", dist_base, pose="FRONTAL")

    retriever = FaissCandidateRetriever(index_manager=manager, default_top_k=5)
    mock_repo = MockRepo({"STU_POSE_01": {"canonical": canonical, "variants": variants}})
    verifier = CandidateVerifier(biometric_repo=mock_repo, match_threshold=0.65)

    # Test 1: Query with Left Profile (yaw = -28.0°)
    left_noise = rng.randn(512).astype(np.float32)
    left_noise /= np.linalg.norm(left_noise)
    left_probe = (0.94 * variant_vectors["LEFT_PROFILE"] + 0.06 * left_noise).astype(np.float32)
    left_probe /= np.linalg.norm(left_probe)

    cands_left = retriever.retrieve_candidates(left_probe, top_k=5)
    decision_left = verifier.verify_candidates(left_probe, cands_left, query_yaw=-28.0)

    assert decision_left.is_verified is True
    assert decision_left.student_id == "STU_POSE_01"
    assert decision_left.best_matching_pose == "LEFT_PROFILE"
    assert decision_left.best_variant_similarity > 0.88

    # Test 2: Query with Right Profile (yaw = +30.0°)
    right_noise = rng.randn(512).astype(np.float32)
    right_noise /= np.linalg.norm(right_noise)
    right_probe = (0.93 * variant_vectors["RIGHT_PROFILE"] + 0.07 * right_noise).astype(np.float32)
    right_probe /= np.linalg.norm(right_probe)

    cands_right = retriever.retrieve_candidates(right_probe, top_k=5)
    decision_right = verifier.verify_candidates(right_probe, cands_right, query_yaw=30.0)

    assert decision_right.is_verified is True
    assert decision_right.student_id == "STU_POSE_01"
    assert decision_right.best_matching_pose == "RIGHT_PROFILE"


# ============================================================================
# Task 37: Occlusion Recovery Test (Glasses, masks, partial crops)
# ============================================================================
def test_occlusion_recovery_and_partial_face():
    """Verifies that face recognition degrades gracefully under partial occlusions
    (e.g., lower face mask, eyewear) when sufficient unoccluded biometric features remain."""
    rng = np.random.RandomState(137)
    manager = FaissIndexManager(dim=512)

    canonical = rng.randn(512).astype(np.float32)
    canonical /= np.linalg.norm(canonical)
    manager.add_vector("STU_OCC_01", canonical, pose="FRONTAL")

    retriever = FaissCandidateRetriever(index_manager=manager, default_top_k=5)
    mock_repo = MockRepo({"STU_OCC_01": {"canonical": canonical, "variants": []}})
    verifier = CandidateVerifier(biometric_repo=mock_repo, match_threshold=0.62)

    # 1. Mild Occlusion (Glasses / Forehead coverage: 80% biometric retention)
    # Cosine similarity remains ~0.78
    noise_mild = rng.randn(512).astype(np.float32)
    noise_mild /= np.linalg.norm(noise_mild)
    probe_mild = (0.80 * canonical + 0.20 * noise_mild).astype(np.float32)
    probe_mild /= np.linalg.norm(probe_mild)

    cands = retriever.retrieve_candidates(probe_mild, top_k=3)
    res_mild = verifier.verify_candidates(probe_mild, cands, query_yaw=0.0)
    assert res_mild.is_verified is True
    assert res_mild.student_id == "STU_OCC_01"
    assert res_mild.composite_similarity >= 0.65

    # 2. Severe Occlusion (Heavy full-face scarf: 40% retention, 60% noise)
    noise_severe = rng.randn(512).astype(np.float32)
    noise_severe /= np.linalg.norm(noise_severe)
    probe_severe = (0.40 * canonical + 0.60 * noise_severe).astype(np.float32)
    probe_severe /= np.linalg.norm(probe_severe)

    cands_sev = retriever.retrieve_candidates(probe_severe, top_k=3)
    res_sev = verifier.verify_candidates(probe_severe, cands_sev, query_yaw=0.0)
    # Severe occlusion should be rejected to prevent false positive match
    assert res_sev.is_verified is False


# ============================================================================
# Task 38: Similar Faces Separation Test (Lookalike / Twins Margin Separation)
# ============================================================================
def test_similar_faces_and_margin_separation():
    """Verifies that lookalikes/twins sharing high similarity (0.72) are cleanly
    disambiguated using margin thresholds or held in ambiguity until temporal confirmation."""
    rng = np.random.RandomState(38)
    manager = FaissIndexManager(dim=512)

    # Base twin structure
    shared_ancestor = rng.randn(512).astype(np.float32)
    shared_ancestor /= np.linalg.norm(shared_ancestor)

    # Twin A and Twin B are close (cos_sim ~ 0.73)
    noise_a = rng.randn(512).astype(np.float32)
    noise_a /= np.linalg.norm(noise_a)
    twin_a = (0.75 * shared_ancestor + 0.25 * noise_a).astype(np.float32)
    twin_a /= np.linalg.norm(twin_a)

    noise_b = rng.randn(512).astype(np.float32)
    noise_b /= np.linalg.norm(noise_b)
    twin_b = (0.75 * shared_ancestor + 0.25 * noise_b).astype(np.float32)
    twin_b /= np.linalg.norm(twin_b)

    # Verify high similarity between twins
    twin_sim = float(np.dot(twin_a, twin_b))
    assert 0.65 <= twin_sim <= 0.95

    # Index both twins
    manager.add_vector("TWIN_A", twin_a, pose="FRONTAL")
    manager.add_vector("TWIN_B", twin_b, pose="FRONTAL")

    retriever = FaissCandidateRetriever(index_manager=manager, default_top_k=5)
    mock_repo = MockRepo({
        "TWIN_A": {"canonical": twin_a, "variants": []},
        "TWIN_B": {"canonical": twin_b, "variants": []}
    })
    # Strict verifier requiring 0.05 margin between #1 and #2 candidate
    verifier = CandidateVerifier(biometric_repo=mock_repo, match_threshold=0.68, min_margin=0.05)

    # Probe of Twin A with slight noise
    probe_noise = rng.randn(512).astype(np.float32)
    probe_noise /= np.linalg.norm(probe_noise)
    probe_a = (0.95 * twin_a + 0.05 * probe_noise).astype(np.float32)
    probe_a /= np.linalg.norm(probe_a)

    cands = retriever.retrieve_candidates(probe_a, top_k=5)
    res = verifier.verify_candidates(probe_a, cands, query_yaw=0.0)

    # Twin A should match with margin exceeding Twin B
    assert res.is_verified is True
    assert res.student_id == "TWIN_A"
    assert res.margin_to_second > 0.05


# ============================================================================
# Task 39: Unknown Visitors Audit Test (Intruder isolation vs degraded frames)
# ============================================================================
def test_unknown_visitors_audit_and_intrusion_logging():
    """Verifies that genuine unregistered visitors trigger alarms, while blurry/dark
    enrolled frames are classified as poor quality without false intruder alarms."""
    classifier = UnknownPersonClassifier(
        unknown_threshold=0.52,
        uncertain_threshold=0.65,
        min_quality_for_confirmed_unknown=0.70
    )

    # Scenario 1: Unregistered Stranger walking in (sharp, well-lit, but max DB similarity = 0.38)
    stranger_res = classifier.classify_observation(
        max_similarity=0.38,
        face_quality_score=0.92,
        face_width=115.0,
        blur_score=160.0,
        temporal_track_frames=3
    )
    assert stranger_res.is_unknown_visitor is True
    assert stranger_res.classification == "GENUINE_UNKNOWN"
    assert stranger_res.action_required == "DISPATCH_ALARM"

    # Scenario 2: Enrolled student captured at distance with motion blur
    # Low similarity (0.48), but face width is 62px and blur is 70.0
    degraded_res = classifier.classify_observation(
        max_similarity=0.48,
        face_quality_score=0.45,
        face_width=62.0,
        blur_score=70.0,
        temporal_track_frames=1
    )
    # Must NOT brand enrolled student as intruder!
    assert degraded_res.is_unknown_visitor is False
    assert degraded_res.classification == "POOR_QUALITY_FACE"
    assert degraded_res.action_required == "RE_ACQUIRE_FACE"


# ============================================================================
# Task 40: Cross-Camera Identity Consistency Test (Spatial Handover)
# ============================================================================
def test_cross_camera_identity_consistency():
    """Verifies that a student moving across camera boundaries (Corridor C1 -> Classroom C203)
    maintains identity continuity via temporal memory and cross-camera track confirmation."""
    imm = IdentityMemoryManager(min_confirm_hits=3, confirm_similarity_thresh=0.65)
    rng = np.random.RandomState(40)

    student_vec = rng.randn(512).astype(np.float32)
    student_vec /= np.linalg.norm(student_vec)

    # Camera 1 (Corridor Entry): Track 101
    for frame_idx in range(3):
        noise = rng.randn(512).astype(np.float32)
        noise /= np.linalg.norm(noise)
        obs_vec = (0.92 * student_vec + 0.08 * noise).astype(np.float32)
        obs_vec /= np.linalg.norm(obs_vec)

        mem = imm.update_track_observation(
            track_id=101,
            embedding=obs_vec,
            candidate_id="STU_CAMPUS_99",
            similarity=0.74,
            quality=0.88,
            modality="FACE"
        )

    # Track 101 confirmed on Camera 1
    assert imm.is_confirmed(track_id=101) is True
    assert imm.get_confirmed_identity(track_id=101) == "STU_CAMPUS_99"

    # Camera 2 (Classroom Door): Student appears as new local Track 202
    # Handover verification: First frame on Camera 2 is corroborated by identity memory
    c2_noise = rng.randn(512).astype(np.float32)
    c2_noise /= np.linalg.norm(c2_noise)
    c2_vec = (0.90 * student_vec + 0.10 * c2_noise).astype(np.float32)
    c2_vec /= np.linalg.norm(c2_vec)

    for frame_idx in range(3):
        mem2 = imm.update_track_observation(
            track_id=202,
            embedding=c2_vec,
            candidate_id="STU_CAMPUS_99",
            similarity=0.72,
            quality=0.85,
            modality="FACE_BODY_FUSED"
        )

    # Track 202 on Camera 2 cleanly locks to identical student
    assert imm.is_confirmed(track_id=202) is True
    assert imm.get_confirmed_identity(track_id=202) == "STU_CAMPUS_99"
