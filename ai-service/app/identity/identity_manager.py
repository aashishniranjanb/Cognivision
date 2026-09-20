"""Temporal Identity Manager: Smooths track observations over time to confirm identity or flag uncertainty."""
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

@dataclass
class IdentityDecision:
    student_id: Optional[str]      # e.g., 'STU001' or None
    state: str                     # 'UNKNOWN', 'TENTATIVE', 'CONFIRMED', 'UNCERTAIN'
    fused_score: float             # identity_score * reliability_score
    observation_count: int

class TemporalIdentityManager:
    def __init__(
        self,
        confirm_threshold: float = 0.65,
        min_observations: int = 3,
        window_size: int = 8
    ):
        self.confirm_threshold = confirm_threshold
        self.min_observations = min_observations
        self.window_size = window_size
        
        # track_id -> deque of (candidate_id, similarity, reliability)
        self.track_evidence: Dict[int, deque] = defaultdict(lambda: deque(maxlen=window_size))
        # track_id -> current IdentityDecision
        self.current_decisions: Dict[int, IdentityDecision] = {}

    def update_track_evidence(
        self,
        track_id: int,
        candidate_id: Optional[str],
        similarity: float,
        reliability: float
    ) -> IdentityDecision:
        """Adds a new observation for track_id and recalculates state."""
        if candidate_id is not None:
            self.track_evidence[track_id].append((candidate_id, similarity, reliability))

        evidence = self.track_evidence[track_id]
        if len(evidence) == 0:
            decision = IdentityDecision(None, "UNKNOWN", 0.0, 0)
            self.current_decisions[track_id] = decision
            return decision

        # Aggregate candidate evidence
        candidate_scores = defaultdict(list)
        candidate_reliabilities = defaultdict(list)

        for cid, sim, rel in evidence:
            candidate_scores[cid].append(sim)
            candidate_reliabilities[cid].append(rel)

        # Candidate with highest frequency and average score
        best_cid = None
        best_fused_score = 0.0

        for cid, sims in candidate_scores.items():
            avg_sim = sum(sims) / len(sims)
            avg_rel = sum(candidate_reliabilities[cid]) / len(candidate_reliabilities[cid])
            fused = avg_sim * avg_rel  # Reliability-aware product

            if fused > best_fused_score:
                best_fused_score = fused
                best_cid = cid

        obs_count = len(evidence)

        # State transitions
        if best_fused_score < 0.45 or best_cid is None:
            state = "UNKNOWN"
            best_cid = None
        elif obs_count < self.min_observations:
            state = "TENTATIVE"
        elif best_fused_score >= self.confirm_threshold:
            state = "CONFIRMED"
        else:
            state = "UNCERTAIN"

        decision = IdentityDecision(
            student_id=best_cid,
            state=state,
            fused_score=best_fused_score,
            observation_count=obs_count
        )
        self.current_decisions[track_id] = decision
        return decision

    def purge_track(self, track_id: int):
        if track_id in self.track_evidence:
            del self.track_evidence[track_id]
        if track_id in self.current_decisions:
            del self.current_decisions[track_id]
