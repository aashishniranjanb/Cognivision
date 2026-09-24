"""Track Identity Memory: Manages per-track biometric history buffers, temporal identity locking, and modality tracking."""
import time
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np

from app.face.temporal_aggregator import TemporalEmbeddingAggregator, AggregatedTrackFeature

@dataclass
class IdentityMemory:
    track_id: int
    student_id: Optional[str] = None
    confirmed: bool = False
    confirmed_count: int = 0
    confidence: float = 0.0
    embedding_history: deque = field(default_factory=lambda: deque(maxlen=20))
    similarity_history: deque = field(default_factory=lambda: deque(maxlen=20))
    quality_history: deque = field(default_factory=lambda: deque(maxlen=20))
    modality_history: deque = field(default_factory=lambda: deque(maxlen=20))
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    decay_counter: int = 0  # Number of frames with occluded/missing face

class IdentityMemoryManager:
    def __init__(
        self,
        min_confirm_hits: int = 3,
        confirm_similarity_thresh: float = 0.65,
        max_decay_frames: int = 25,
        aggregator: Optional[TemporalEmbeddingAggregator] = None
    ):
        self.min_confirm_hits = min_confirm_hits
        self.confirm_similarity_thresh = confirm_similarity_thresh
        self.max_decay_frames = max_decay_frames
        self.aggregator = aggregator or TemporalEmbeddingAggregator()
        self.tracks: Dict[int, IdentityMemory] = {}

    def get_or_create_memory(self, track_id: int) -> IdentityMemory:
        if track_id not in self.tracks:
            self.tracks[track_id] = IdentityMemory(track_id=track_id)
        return self.tracks[track_id]

    def update_track_observation(
        self,
        track_id: int,
        embedding: Optional[np.ndarray],
        candidate_id: Optional[str],
        similarity: float,
        quality: float,
        modality: str = "FACE"
    ) -> IdentityMemory:
        """Updates biometric evidence for a tracked person."""
        mem = self.get_or_create_memory(track_id)
        now = time.time()
        mem.last_seen = now

        if embedding is not None and embedding.size > 0:
            mem.embedding_history.append(embedding)
            mem.quality_history.append(quality)
            mem.decay_counter = 0
        else:
            mem.decay_counter += 1

        mem.similarity_history.append(similarity)
        mem.modality_history.append(modality)

        # Identity Confirmation Logic
        if candidate_id and similarity >= self.confirm_similarity_thresh:
            if mem.student_id == candidate_id:
                mem.confirmed_count += 1
            else:
                mem.student_id = candidate_id
                mem.confirmed_count = 1

            if mem.confirmed_count >= self.min_confirm_hits:
                mem.confirmed = True
                mem.confidence = float(np.mean(list(mem.similarity_history)[-self.min_confirm_hits:]))
        elif not mem.confirmed:
            # If not yet confirmed and similarity drops, reset candidate
            if similarity < 0.45:
                mem.confirmed_count = max(0, mem.confirmed_count - 1)
                if mem.confirmed_count == 0:
                    mem.student_id = None

        return mem

    def get_aggregated_track_feature(self, track_id: int) -> Optional[AggregatedTrackFeature]:
        if track_id not in self.tracks:
            return None
        mem = self.tracks[track_id]
        if not mem.embedding_history:
            return None
        return self.aggregator.aggregate_track_embeddings(
            list(mem.embedding_history),
            list(mem.quality_history)
        )

    def is_confirmed(self, track_id: int) -> bool:
        if track_id not in self.tracks:
            return False
        return self.tracks[track_id].confirmed

    def get_confirmed_identity(self, track_id: int) -> Optional[str]:
        if track_id not in self.tracks:
            return None
        mem = self.tracks[track_id]
        return mem.student_id if mem.confirmed else None

    def clean_stale_tracks(self, max_age_sec: float = 30.0) -> int:
        now = time.time()
        to_del = [tid for tid, m in self.tracks.items() if (now - m.last_seen) > max_age_sec]
        for tid in to_del:
            del self.tracks[tid]
        return len(to_del)
