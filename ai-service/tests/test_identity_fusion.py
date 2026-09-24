"""Tests for Step 5 — Face + Body Adaptive Fusion & Decision Levels (Plan 24)."""
import time
import pytest
from app.fusion.observation import ModalityObservation
from app.fusion.adaptive_fusion import AdaptiveFusionEngine, FusedIdentityDecision

def test_high_confidence_fusion():
    engine = AdaptiveFusionEngine()
    obs = [
        ModalityObservation(
            modality="face",
            candidate_id="STU001",
            identity_score=0.95,
            reliability=0.92,
            track_id=1,
            timestamp=time.time()
        ),
        ModalityObservation(
            modality="body",
            candidate_id="STU001",
            identity_score=0.88,
            reliability=0.85,
            track_id=1,
            timestamp=time.time()
        )
    ]
    fused = engine.fuse(track_id=1, observations=obs)
    assert fused.decision == "STU001"
    assert fused.decision_level == "HIGH_CONFIDENCE"
    assert fused.confidence > 0.85

def test_occluded_face_shifts_weight_to_body():
    """Plan 24: Occluded face: Face 0.20, Body 0.80 weight shift."""
    engine = AdaptiveFusionEngine()
    obs = [
        ModalityObservation(
            modality="face",
            candidate_id="STU002",
            identity_score=0.70,
            reliability=0.20,
            track_id=2,
            timestamp=time.time()
        ),
        ModalityObservation(
            modality="body",
            candidate_id="STU001",
            identity_score=0.86,
            reliability=0.85,
            track_id=2,
            timestamp=time.time()
        )
    ]
    fused = engine.fuse(track_id=2, observations=obs)
    # Body should heavily dominate the weighting
    assert fused.modality_weights["body"] > fused.modality_weights["face"]
    assert fused.decision == "STU001"
    assert fused.decision_level in ("HIGH_CONFIDENCE", "MEDIUM_CONFIDENCE")

def test_both_modalities_bad_results_in_uncertain():
    """Plan 24: Both bad -> UNCERTAIN, do not force uncertain observations into a student ID."""
    engine = AdaptiveFusionEngine()
    obs = [
        ModalityObservation(
            modality="face",
            candidate_id="STU001",
            identity_score=0.60,
            reliability=0.25,
            track_id=3,
            timestamp=time.time()
        ),
        ModalityObservation(
            modality="body",
            candidate_id="STU001",
            identity_score=0.55,
            reliability=0.30,
            track_id=3,
            timestamp=time.time()
        )
    ]
    fused = engine.fuse(track_id=3, observations=obs)
    assert fused.decision_level == "UNCERTAIN"
    assert fused.decision is None  # Never force an uncertain observation into an identity!

def test_ambiguous_candidate_conflict_is_uncertain():
    """When face and body point to different people with close scores, report UNCERTAIN."""
    engine = AdaptiveFusionEngine()
    obs = [
        ModalityObservation(
            modality="face",
            candidate_id="STU001",
            identity_score=0.62,
            reliability=0.50,
            track_id=4,
            timestamp=time.time()
        ),
        ModalityObservation(
            modality="body",
            candidate_id="STU002",
            identity_score=0.60,
            reliability=0.55,
            track_id=4,
            timestamp=time.time()
        )
    ]
    fused = engine.fuse(track_id=4, observations=obs)
    assert fused.decision_level == "UNCERTAIN"
    assert fused.decision is None

def test_unknown_when_no_valid_observations():
    engine = AdaptiveFusionEngine()
    fused = engine.fuse(track_id=5, observations=[])
    assert fused.decision_level == "UNKNOWN"
    assert fused.decision is None
    assert fused.confidence == 0.0
