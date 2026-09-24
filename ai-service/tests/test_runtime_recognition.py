"""
Tests for Sprint D Runtime Recognition Components:
- TemporalEmbeddingAggregator (Task 21)
- IdentityMemoryManager (Task 22)
- UnknownPersonClassifier (Task 23)
- BiometricConfidenceCalibrator (Task 24)
"""

import pytest
import numpy as np
from app.face.temporal_aggregator import TemporalEmbeddingAggregator
from app.identity.identity_memory import IdentityMemoryManager
from app.face.unknown_rejector import UnknownPersonClassifier
from app.face.confidence_calibrator import BiometricConfidenceCalibrator


def test_temporal_embedding_aggregator():
    agg = TemporalEmbeddingAggregator(decay_factor=0.9, max_frames=5)
    rng = np.random.RandomState(42)

    base = rng.randn(512).astype(np.float32)
    base /= np.linalg.norm(base)

    noise1 = rng.randn(512).astype(np.float32)
    noise1 /= np.linalg.norm(noise1)
    noisy1 = (0.95 * base + 0.05 * noise1).astype(np.float32)
    noisy1 /= np.linalg.norm(noisy1)

    noise2 = rng.randn(512).astype(np.float32)
    noise2 /= np.linalg.norm(noise2)
    noisy2 = (0.92 * base + 0.08 * noise2).astype(np.float32)
    noisy2 /= np.linalg.norm(noisy2)

    res = agg.aggregate_track_embeddings(
        embeddings=[base, noisy1, noisy2],
        qualities=[0.9, 0.7, 0.95]
    )

    assert res.sample_count == 3
    assert res.embedding.shape == (512,)
    # Verify unit norm
    norm = np.linalg.norm(res.embedding)
    assert pytest.approx(norm, abs=1e-5) == 1.0

    # Aggregated vector should have high similarity with base
    cos_sim = float(np.dot(res.embedding, base))
    assert cos_sim > 0.95
    assert res.temporal_stability > 0.85

    # Empty list returns empty result
    empty_res = agg.aggregate_track_embeddings([])
    assert empty_res.sample_count == 0


def test_identity_memory_manager():
    imm = IdentityMemoryManager(min_confirm_hits=3, confirm_similarity_thresh=0.65)
    rng = np.random.RandomState(42)
    dummy_emb = rng.randn(512).astype(np.float32)
    dummy_emb /= np.linalg.norm(dummy_emb)

    # Observation 1: hit 1
    mem = imm.update_track_observation(
        track_id=10,
        embedding=dummy_emb,
        candidate_id="STU_001",
        similarity=0.72,
        quality=0.88
    )
    assert not mem.confirmed
    assert mem.confirmed_count == 1
    assert mem.student_id == "STU_001"

    # Observation 2: hit 2
    mem = imm.update_track_observation(
        track_id=10,
        embedding=dummy_emb,
        candidate_id="STU_001",
        similarity=0.75,
        quality=0.89
    )
    assert not mem.confirmed
    assert mem.confirmed_count == 2

    # Observation 3: hit 3 reaches min_confirm_hits -> locks identity
    mem = imm.update_track_observation(
        track_id=10,
        embedding=dummy_emb,
        candidate_id="STU_001",
        similarity=0.71,
        quality=0.85
    )
    assert mem.confirmed is True
    assert mem.confirmed_count == 3

    # Confirmed identity retrieval
    confirmed_id = imm.get_confirmed_identity(track_id=10)
    assert confirmed_id == "STU_001"
    assert imm.is_confirmed(track_id=10) is True

    # Check track aggregation
    agg_feat = imm.get_aggregated_track_feature(track_id=10)
    assert agg_feat is not None
    assert agg_feat.sample_count == 3


def test_unknown_person_classifier():
    classifier = UnknownPersonClassifier(
        unknown_threshold=0.52,
        uncertain_threshold=0.65,
        min_quality_for_confirmed_unknown=0.70
    )

    # Case 1: High similarity -> KNOWN_STUDENT
    res_known = classifier.classify_observation(
        max_similarity=0.75,
        face_quality_score=0.85,
        face_width=100.0,
        blur_score=130.0
    )
    assert res_known.classification == "KNOWN_STUDENT"
    assert res_known.is_unknown_visitor is False
    assert res_known.action_required == "NONE"

    # Case 2: Low similarity but degraded face -> POOR_QUALITY_FACE (not unknown!)
    res_degraded = classifier.classify_observation(
        max_similarity=0.45,
        face_quality_score=0.50,
        face_width=60.0,
        blur_score=70.0
    )
    assert res_degraded.classification == "POOR_QUALITY_FACE"
    assert res_degraded.is_unknown_visitor is False
    assert res_degraded.action_required == "RE_ACQUIRE_FACE"

    # Case 3: Low similarity with high quality face and sustained frames -> GENUINE_UNKNOWN
    res_unknown = classifier.classify_observation(
        max_similarity=0.40,
        face_quality_score=0.90,
        face_width=110.0,
        blur_score=150.0,
        temporal_track_frames=3
    )
    assert res_unknown.classification == "GENUINE_UNKNOWN"
    assert res_unknown.is_unknown_visitor is True
    assert res_unknown.action_required == "DISPATCH_ALARM"


def test_confidence_calibrator():
    calibrator = BiometricConfidenceCalibrator()

    # Optimal conditions + high similarity
    conf_optimal = calibrator.calibrate(
        raw_cosine_similarity=0.75,
        face_width=120.0,
        blur_score=150.0,
        illumination_score=0.90,
        consecutive_hits=3
    )
    assert 0.85 <= conf_optimal <= 1.0

    # Sub-optimal conditions: severe angle, small width, motion blur
    conf_degraded = calibrator.calibrate(
        raw_cosine_similarity=0.75,
        face_width=50.0,      # small face penalty
        blur_score=40.0,      # blur penalty
        illumination_score=0.4, # poor illumination
        consecutive_hits=1
    )
    # Calibrated confidence should be significantly penalised
    assert conf_degraded < conf_optimal
    assert conf_degraded < 0.65
