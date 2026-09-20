"""Evaluation Harness: Tests 5 Difficult CCTV Scenarios (Occlusion, Lighting, Crossing, Unknown, Scale)."""
import time
from app.fusion.observation import ModalityObservation
from app.fusion.adaptive_fusion import AdaptiveFusionEngine
from app.evaluation.metrics import EvaluationMetricsEngine

class ScenarioEvaluationHarness:
    def __init__(self):
        self.fusion = AdaptiveFusionEngine(acceptance_threshold=0.48)
        self.metrics = EvaluationMetricsEngine()

    def run_all_scenarios(self) -> dict:
        results = {}
        results["test_a_face_occlusion"] = self.scenario_face_occlusion()
        results["test_b_low_lighting"] = self.scenario_low_lighting()
        results["test_c_crossing_continuity"] = self.scenario_crossing()
        results["test_d_unknown_rejection"] = self.scenario_unknown_rejection()
        results["test_e_similar_clothing"] = self.scenario_similar_clothing()
        return results

    def scenario_face_occlusion(self) -> bool:
        """Test A: Face completely occluded -> Body Re-ID takes majority weight and retains identity."""
        obs = [
            ModalityObservation("face", "STU001", identity_score=0.85, reliability=0.10, track_id=1, timestamp=time.time()),
            ModalityObservation("body", "STU001", identity_score=0.82, reliability=0.85, track_id=1, timestamp=time.time())
        ]
        decision = self.fusion.fuse(1, obs)
        self.metrics.record_prediction(ground_truth_id="STU001", predicted_id=decision.decision)
        return decision.decision == "STU001" and decision.modality_weights.get("body", 0) > decision.modality_weights.get("face", 0)

    def scenario_low_lighting(self) -> bool:
        """Test B: Low lighting suppresses face reliability; body Re-ID weight increases dynamically."""
        obs = [
            ModalityObservation("face", "STU002", identity_score=0.82, reliability=0.35, track_id=2, timestamp=time.time()),
            ModalityObservation("body", "STU002", identity_score=0.80, reliability=0.80, track_id=2, timestamp=time.time())
        ]
        decision = self.fusion.fuse(2, obs)
        self.metrics.record_prediction(ground_truth_id="STU002", predicted_id=decision.decision)
        return decision.decision == "STU002"

    def scenario_crossing(self) -> bool:
        """Test C: Two crossing people retain independent identities."""
        obs1 = [
            ModalityObservation("face", "STU001", 0.90, 0.88, 17, time.time()),
            ModalityObservation("body", "STU001", 0.82, 0.75, 17, time.time())
        ]
        obs2 = [
            ModalityObservation("face", "STU003", 0.88, 0.85, 22, time.time()),
            ModalityObservation("body", "STU003", 0.80, 0.78, 22, time.time())
        ]
        d1 = self.fusion.fuse(17, obs1)
        d2 = self.fusion.fuse(22, obs2)
        self.metrics.record_prediction("STU001", d1.decision)
        self.metrics.record_prediction("STU003", d2.decision)
        return d1.decision == "STU001" and d2.decision == "STU003"

    def scenario_unknown_rejection(self) -> bool:
        """Test D: Unknown person must be rejected as UNKNOWN (Never forced into enrolled student)."""
        obs = [
            ModalityObservation("face", "STU001", identity_score=0.25, reliability=0.85, track_id=99, timestamp=time.time()),
            ModalityObservation("body", "STU002", identity_score=0.30, reliability=0.70, track_id=99, timestamp=time.time())
        ]
        decision = self.fusion.fuse(99, obs)
        # Ground truth is None (unknown), system should predict None/UNKNOWN
        self.metrics.record_prediction(ground_truth_id=None, predicted_id=decision.decision)
        return decision.decision is None or decision.decision == "UNKNOWN"

    def scenario_similar_clothing(self) -> bool:
        """Test E: Conflicting body appearance resolves via high-reliability face match."""
        obs = [
            ModalityObservation("face", "STU001", identity_score=0.92, reliability=0.92, track_id=5, timestamp=time.time()),
            ModalityObservation("body", "STU004", identity_score=0.70, reliability=0.60, track_id=5, timestamp=time.time())
        ]
        decision = self.fusion.fuse(5, obs)
        self.metrics.record_prediction("STU001", decision.decision)
        return decision.decision == "STU001"
