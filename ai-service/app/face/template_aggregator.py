"""Quality-Weighted Template Aggregator: Synthesizes a robust 512-D canonical identity centroid from enrollment variants."""
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AggregatedTemplateResult:
    canonical_embedding: np.ndarray
    enrollment_quality: float
    enrolled_count: int
    intra_class_compactness: float
    similarity_to_centroid: List[float]
    metrics: Dict[str, Any] = field(default_factory=dict)

class TemplateAggregator:
    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim

    def aggregate(
        self,
        embeddings: List[np.ndarray],
        quality_scores: Optional[List[float]] = None
    ) -> AggregatedTemplateResult:
        """Aggregates a set of 512-D embeddings into a single quality-weighted canonical centroid."""
        if not embeddings:
            return AggregatedTemplateResult(
                canonical_embedding=np.zeros(self.embedding_dim, dtype=np.float32),
                enrollment_quality=0.0,
                enrolled_count=0,
                intra_class_compactness=0.0,
                similarity_to_centroid=[]
            )

        n = len(embeddings)
        arr = np.array(embeddings, dtype=np.float32)

        # Normalize input vectors
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms

        # Quality weights: default to uniform if not specified or all zero
        if quality_scores is None or len(quality_scores) != n:
            weights = np.ones(n, dtype=np.float32)
        else:
            weights = np.array(quality_scores, dtype=np.float32)
            if np.sum(weights) < 1e-4:
                weights = np.ones(n, dtype=np.float32)

        # Quality-weighted sum: Σ(q_i * e_i) / Σ(q_i)
        weights_sum = np.sum(weights)
        weighted_sum = np.sum(arr * weights[:, np.newaxis], axis=0) / weights_sum

        # L2 unit normalization of centroid
        centroid_norm = np.linalg.norm(weighted_sum)
        if centroid_norm > 1e-6:
            canonical = weighted_sum / centroid_norm
        else:
            canonical = weighted_sum

        # Calculate cosine similarity of each variant to canonical centroid
        sims_to_centroid = np.dot(arr, canonical).tolist()
        mean_compactness = float(np.mean(sims_to_centroid))
        std_compactness = float(np.std(sims_to_centroid))

        mean_quality = float(np.mean(weights)) if quality_scores else 0.85

        return AggregatedTemplateResult(
            canonical_embedding=canonical.astype(np.float32),
            enrollment_quality=round(mean_quality, 3),
            enrolled_count=n,
            intra_class_compactness=round(mean_compactness, 3),
            similarity_to_centroid=[round(s, 4) for s in sims_to_centroid],
            metrics={
                "compactness_std": round(std_compactness, 4),
                "weights_used": [round(float(w), 3) for w in weights],
                "centroid_norm": round(float(centroid_norm), 4)
            }
        )
