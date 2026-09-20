"""Robust Temporal Identity Manager with Identity Memory, Reliability Weighting, and Anomaly Detection."""
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple, List

@dataclass
class IdentityObservation:
    track_id: int
    student_id: Optional[str]
    identity_similarity: float
    face_reliability: float
    timestamp: float
    status: str

@dataclass
class AnomalyEvent:
    anomaly_type: str       # "UNKNOWN_PERSON", "LOW_FACE_QUALITY", "IDENTITY_UNCERTAIN", "TRACKED_NO_FACE"
    track_id: int
    timestamp: float
    details: str

class RobustIdentityManager:
    def __init__(
        self,
        confirm_threshold: float = 0.55,
        min_confirmed_hits: int = 3,
        memory_decay_frames: int = 15,
        window_size: int = 10
    ):
        self.confirm_threshold = confirm_threshold
        self.min_confirmed_hits = min_confirmed_hits
        self.memory_decay_frames = memory_decay_frames
        self.window_size = window_size

        # track_id -> deque of IdentityObservation
        self.track_history: Dict[int, deque[IdentityObservation]] = defaultdict(lambda: deque(maxlen=window_size))
        # track_id -> confirmed student_id memory (preserves identity through temporary face disappearance)
        self.confirmed_memory: Dict[int, str] = {}
        # track_id -> consecutive frames without face
        self.missing_face_counters: Dict[int, int] = defaultdict(int)
        # Recent anomaly events for auditing
        self.anomalies: List[AnomalyEvent] = []

    def update_observation(
        self,
        track_id: int,
        candidate_id: Optional[str],
        similarity: float,
        reliability: float
    ) -> Tuple[str, Optional[str], float]:
        """
        Updates evidence for track_id.
        Returns (status, student_id, fused_confidence).
        Status is one of: 'CONFIRMED', 'TENTATIVE', 'UNKNOWN', 'UNCERTAIN', 'TRACKED_NO_FACE'.
        """
        now = time.time()

        # Case 1: Person tracked but face not visible (e.g. turned away or occluded)
        if candidate_id is None or reliability < 0.20:
            self.missing_face_counters[track_id] += 1
            # If identity was previously confirmed, keep it alive in memory across brief occlusions
            if track_id in self.confirmed_memory and self.missing_face_counters[track_id] <= self.memory_decay_frames:
                return "CONFIRMED", self.confirmed_memory[track_id], 0.70
            
            if self.missing_face_counters[track_id] > self.memory_decay_frames:
                self.confirmed_memory.pop(track_id, None)
                self._record_anomaly("TRACKED_NO_FACE", track_id, f"Face absent for {self.missing_face_counters[track_id]} consecutive frames")
                return "UNKNOWN", None, 0.0

            return "TENTATIVE", self.confirmed_memory.get(track_id), 0.30

        # Case 2: Face is visible
        self.missing_face_counters[track_id] = 0

        # Low-quality face observation filter (Requirement: low quality reduces influence, not false accept)
        if reliability < 0.40:
            self._record_anomaly("LOW_FACE_QUALITY", track_id, f"Face reliability is poor ({reliability:.2f})")

        obs = IdentityObservation(
            track_id=track_id,
            student_id=candidate_id,
            identity_similarity=similarity,
            face_reliability=reliability,
            timestamp=now,
            status="TENTATIVE"
        )
        self.track_history[track_id].append(obs)

        # Reliability-aware evidence weighting: effective weight = similarity * reliability
        candidate_weights = defaultdict(float)
        candidate_counts = defaultdict(int)

        for o in self.track_history[track_id]:
            if o.student_id:
                candidate_weights[o.student_id] += (o.identity_similarity * o.face_reliability)
                candidate_counts[o.student_id] += 1

        if not candidate_weights:
            return "UNKNOWN", None, 0.0

        # Disagreement check: If multiple distinct candidates compete strongly
        sorted_candidates = sorted(candidate_weights.items(), key=lambda x: x[1], reverse=True)
        top_cand, top_weight = sorted_candidates[0]

        if len(sorted_candidates) > 1:
            runner_up_cand, runner_up_weight = sorted_candidates[1]
            if runner_up_weight > 0.75 * top_weight:
                self._record_anomaly("IDENTITY_UNCERTAIN", track_id, f"Disagreement between {top_cand} and {runner_up_cand}")
                return "UNCERTAIN", None, float(top_weight / candidate_counts[top_cand])

        avg_confidence = top_weight / candidate_counts[top_cand]

        if avg_confidence < 0.35:
            self._record_anomaly("UNKNOWN_PERSON", track_id, f"Similarity below acceptance ({avg_confidence:.2f})")
            return "UNKNOWN", None, avg_confidence

        if candidate_counts[top_cand] >= self.min_confirmed_hits and avg_confidence >= self.confirm_threshold:
            self.confirmed_memory[track_id] = top_cand
            return "CONFIRMED", top_cand, avg_confidence

        return "TENTATIVE", top_cand, avg_confidence

    def _record_anomaly(self, atype: str, track_id: int, details: str):
        evt = AnomalyEvent(atype, track_id, time.time(), details)
        self.anomalies.append(evt)
        if len(self.anomalies) > 30:
            self.anomalies.pop(0)

    def purge_inactive(self, active_track_ids: set):
        to_del = [tid for tid in list(self.track_history.keys()) if tid not in active_track_ids]
        for tid in to_del:
            del self.track_history[tid]
            self.confirmed_memory.pop(tid, None)
            self.missing_face_counters.pop(tid, None)
