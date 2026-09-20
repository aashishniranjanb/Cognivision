"""Track Identity Cache preventing repetitive expensive neural network inference on stable tracks."""
import time
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class CachedTrackIdentity:
    track_id: int
    student_id: Optional[str]
    fused_confidence: float
    state: str                 # "CONFIRMED", "TENTATIVE", "UNKNOWN", "UNCERTAIN"
    last_recognition_time: float
    recognition_frame_count: int
    ttl_seconds: float = 3.0   # Identity refresh period for confirmed tracks

class TrackIdentityCache:
    def __init__(self, ttl_seconds: float = 3.0):
        self.ttl_seconds = ttl_seconds
        # track_id -> CachedTrackIdentity
        self.cache: Dict[int, CachedTrackIdentity] = {}

    def needs_recognition(self, track_id: int) -> bool:
        """Determines if deep face/body recognition is required for this track on the current frame."""
        now = time.time()
        if track_id not in self.cache:
            return True  # Brand new track -> Must run recognition

        entry = self.cache[track_id]
        # Tentative/Uncertain tracks need frequent updates to confirm identity
        if entry.state in ("TENTATIVE", "UNCERTAIN"):
            return True

        # Confirmed tracks only refresh periodically after TTL expires
        if (now - entry.last_recognition_time) > self.ttl_seconds:
            return True

        return False

    def update(self, track_id: int, student_id: Optional[str], confidence: float, state: str):
        now = time.time()
        if track_id not in self.cache:
            self.cache[track_id] = CachedTrackIdentity(
                track_id=track_id,
                student_id=student_id,
                fused_confidence=confidence,
                state=state,
                last_recognition_time=now,
                recognition_frame_count=1,
                ttl_seconds=self.ttl_seconds
            )
        else:
            entry = self.cache[track_id]
            entry.student_id = student_id
            entry.fused_confidence = confidence
            entry.state = state
            entry.last_recognition_time = now
            entry.recognition_frame_count += 1

    def get(self, track_id: int) -> Optional[CachedTrackIdentity]:
        return self.cache.get(track_id)

    def purge_inactive(self, active_track_ids: set):
        to_del = [tid for tid in list(self.cache.keys()) if tid not in active_track_ids]
        for tid in to_del:
            del self.cache[tid]
