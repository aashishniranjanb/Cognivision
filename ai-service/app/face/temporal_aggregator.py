"""Temporal Embedding Aggregator: Blends 512-D ArcFace vectors across track frames with quality weighting and recency decay."""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class AggregatedTrackFeature:
    embedding: np.ndarray
    sample_count: int
    temporal_stability: float  # Cosine coherence across track (0.0 to 1.0)
    mean_quality: float
    weights_sum: float

class TemporalEmbeddingAggregator:
    def __init__(self, decay_factor: float = 0.92, max_frames: int = 15):
        self.decay_factor = decay_factor
        self.max_frames = max_frames

    def aggregate_track_embeddings(
        self,
        embeddings: List[np.ndarray],
        qualities: Optional[List[float]] = None
    ) -> AggregatedTrackFeature:
        """Aggregates a sequence of normalized 512-D embeddings collected across consecutive track frames."""
        if not embeddings:
            return AggregatedTrackFeature(
                embedding=np.zeros(512, dtype=np.float32),
                sample_count=0,
                temporal_stability=0.0,
                mean_quality=0.0,
                weights_sum=0.0
            )

        n = min(len(embeddings), self.max_frames)
        # Take the most recent n embeddings
        recent_embeddings = embeddings[-n:]
        recent_qualities = qualities[-n:] if qualities else [0.85] * n

        arr = np.array(recent_embeddings, dtype=np.float32)
        # Ensure L2 normalized
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms

        # Weights: combination of exponential recency decay and frame optical quality
        # Frame t = n-1 (most recent) gets highest recency weight 1.0, older frames decay
        recency = np.array([self.decay_factor ** (n - 1 - i) for i in range(n)], dtype=np.float32)
        quality = np.array(recent_qualities, dtype=np.float32)
        weights = recency * quality

        if np.sum(weights) < 1e-4:
            weights = np.ones(n, dtype=np.float32)

        # Weighted vector sum
        weights_sum = float(np.sum(weights))
        weighted_vector = np.sum(arr * weights[:, np.newaxis], axis=0) / weights_sum

        # Project back to unit hypersphere
        vec_norm = np.linalg.norm(weighted_vector)
        if vec_norm > 1e-6:
            aggregated_emb = weighted_vector / vec_norm
        else:
            aggregated_emb = weighted_vector

        # Calculate temporal stability: cosine similarity of each frame's vector to the aggregated trajectory
        coherence_scores = np.dot(arr, aggregated_emb)
        temporal_stability = float(np.mean(coherence_scores))
        mean_quality = float(np.mean(recent_qualities))

        return AggregatedTrackFeature(
            embedding=aggregated_emb.astype(np.float32),
            sample_count=n,
            temporal_stability=round(float(np.clip(temporal_stability, 0.0, 1.0)), 4),
            mean_quality=round(mean_quality, 4),
            weights_sum=round(weights_sum, 4)
        )
