"""Reliability-Aware Adaptive Multimodal Fusion Engine (Equations 8 & 11 in PRD)."""
from collections import defaultdict
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import time
import json

from app.fusion.observation import ModalityObservation

@dataclass
class FusedIdentityDecision:
    track_id: int
    decision: Optional[str]        # Confirmed student_id or None
    confidence: float              # Fused identity score [0.0, 1.0]
    modalities_participating: List[str]
    modality_weights: Dict[str, float]
    raw_observations: Dict[str, dict]
    audit_trail: dict
    decision_level: str = "UNKNOWN"  # HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, UNCERTAIN, UNKNOWN

class AdaptiveFusionEngine:
    def __init__(
        self,
        base_weights: Optional[Dict[str, float]] = None,
        acceptance_threshold: float = 0.50,
        high_confidence_threshold: float = 0.75,
        uncertain_threshold: float = 0.35,
        min_reliable_threshold: float = 0.35
    ):
        # Base weights as per PRD: Face: 1.0, Body: 0.85, Gait: 0.70
        self.base_weights = base_weights or {
            "face": 1.0,
            "body": 0.85,
            "gait": 0.70
        }
        self.acceptance_threshold = acceptance_threshold
        self.high_confidence_threshold = high_confidence_threshold
        self.uncertain_threshold = uncertain_threshold
        self.min_reliable_threshold = min_reliable_threshold

    def fuse(self, track_id: int, observations: List[ModalityObservation]) -> FusedIdentityDecision:
        """
        Implements PRD Formula:
          E_m = B_m * R_m
          W_m = E_m / sum(E_j)
          S_fused(s) = sum(W_m * S_m(s))
        Only available modalities with reliability > 0 participate.
        Assigns explicit decision levels: HIGH_CONFIDENCE, MEDIUM_CONFIDENCE, UNCERTAIN, UNKNOWN.
        """
        valid_obs = [o for o in observations if o.reliability > 0.10 and o.candidate_id is not None]

        if not valid_obs:
            return FusedIdentityDecision(
                track_id=track_id,
                decision=None,
                confidence=0.0,
                modalities_participating=[],
                modality_weights={},
                raw_observations={o.modality: o.to_dict() for o in observations},
                audit_trail={"status": "REJECTED_NO_USABLE_MODALITY"},
                decision_level="UNKNOWN"
            )

        # Check if all modalities have poor reliability (both bad -> UNCERTAIN)
        max_reliability = max(o.reliability for o in valid_obs)
        both_bad = len(valid_obs) >= 2 and max_reliability < self.min_reliable_threshold

        # 1. Calculate Effective Weights E_m = B_m * R_m
        effective_weights = {}
        for o in valid_obs:
            b_m = self.base_weights.get(o.modality, 0.5)
            effective_weights[o.modality] = b_m * o.reliability

        sum_e = sum(effective_weights.values())
        if sum_e <= 1e-6:
            sum_e = 1e-6

        # 2. Normalized Weights W_m = E_m / sum(E_j)
        norm_weights = {m: (e / sum_e) for m, e in effective_weights.items()}

        # 3. Calculate candidate score sum: S_fused(s) = sum(W_m * S_m(s))
        candidate_fused_scores = defaultdict(float)
        candidate_weighted_totals = defaultdict(float)

        for o in valid_obs:
            w_m = norm_weights[o.modality]
            candidate_fused_scores[o.candidate_id] += w_m * o.identity_score
            candidate_weighted_totals[o.candidate_id] += w_m

        # Pick candidate with highest fused score
        best_cand, best_score = max(candidate_fused_scores.items(), key=lambda x: x[1])

        # Check for ambiguity: multiple conflicting candidates with close fused scores
        sorted_cands = sorted(candidate_fused_scores.items(), key=lambda x: x[1], reverse=True)
        ambiguous = False
        if len(sorted_cands) > 1:
            margin = sorted_cands[0][1] - sorted_cands[1][1]
            if margin < 0.08 and sorted_cands[0][1] < self.high_confidence_threshold:
                ambiguous = True

        # Determine decision level
        if both_bad or ambiguous:
            decision_level = "UNCERTAIN"
            final_decision = None
        elif best_score >= self.high_confidence_threshold and max_reliability >= 0.50:
            decision_level = "HIGH_CONFIDENCE"
            final_decision = best_cand
        elif best_score >= self.acceptance_threshold:
            decision_level = "MEDIUM_CONFIDENCE"
            final_decision = best_cand
        elif best_score >= self.uncertain_threshold:
            decision_level = "UNCERTAIN"
            final_decision = None
        else:
            decision_level = "UNKNOWN"
            final_decision = None

        audit_trail = {
            "track_id": track_id,
            "decision": final_decision or "UNKNOWN",
            "decision_level": decision_level,
            "modalities": {o.modality: o.to_dict() for o in observations},
            "fusion": {
                "decision": best_cand,
                "confidence": round(best_score, 4),
                "weights": {m: round(w, 4) for m, w in norm_weights.items()},
                "both_bad": both_bad,
                "ambiguous": ambiguous
            }
        }

        return FusedIdentityDecision(
            track_id=track_id,
            decision=final_decision,
            confidence=best_score,
            modalities_participating=list(norm_weights.keys()),
            modality_weights=norm_weights,
            raw_observations={o.modality: o.to_dict() for o in observations},
            audit_trail=audit_trail,
            decision_level=decision_level
        )
