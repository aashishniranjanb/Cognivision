"""Comprehensive Suite Testing Week 5 Evaluation Scenarios and Identity Cache."""
from app.evaluation.scenarios import ScenarioEvaluationHarness
from app.optimization.identity_cache import TrackIdentityCache

def test_scenario_harness():
    harness = ScenarioEvaluationHarness()
    results = harness.run_all_scenarios()
    
    assert results["test_a_face_occlusion"] is True
    assert results["test_b_low_lighting"] is True
    assert results["test_c_crossing_continuity"] is True
    assert results["test_d_unknown_rejection"] is True
    assert results["test_e_similar_clothing"] is True

    report = harness.metrics.compute_report()
    assert report.correct_identifications >= 4
    assert report.false_acceptances == 0
    assert report.unknown_rejection_rate == 1.0

def test_identity_cache_selective_inference():
    cache = TrackIdentityCache(ttl_seconds=1.0)
    
    # Brand new track -> Needs recognition
    assert cache.needs_recognition(17) is True

    # After update to CONFIRMED -> Does NOT need recognition immediately
    cache.update(17, "STU001", confidence=0.88, state="CONFIRMED")
    assert cache.needs_recognition(17) is False
