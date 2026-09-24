"""Embedding Outlier Rejection: Identifies and purges contaminated/noisy embedding samples via pairwise cosine similarity clustering."""
import numpy as np
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass, field

@dataclass
class OutlierFilterResult:
    accepted_indices: List[int]
    rejected_indices: List[int]
    pairwise_matrix: List[List[float]]
    mean_intra_similarity: float
    rejection_reasons: Dict[int, str] = field(default_factory=dict)

class EmbeddingOutlierFilter:
    def __init__(self, min_intra_similarity: float = 0.50, sigma_threshold: float = 2.0):
        self.min_intra_similarity = min_intra_similarity
        self.sigma_threshold = sigma_threshold

    def filter_outliers(
        self,
        embeddings: List[np.ndarray],
        quality_scores: Optional[List[float]] = None
    ) -> OutlierFilterResult:
        """Filters out outlier embeddings that do not belong to the identity cluster."""
        n = len(embeddings)
        if n == 0:
            return OutlierFilterResult([], [], [], 0.0)
        if n <= 2:
            # Not enough samples to statistically isolate an outlier, accept all
            matrix = self._compute_similarity_matrix(embeddings)
            mean_sim = float(np.mean(matrix)) if n > 0 else 1.0
            return OutlierFilterResult(
                accepted_indices=list(range(n)),
                rejected_indices=[],
                pairwise_matrix=matrix.tolist(),
                mean_intra_similarity=mean_sim
            )

        # 1. Compute NxN Pairwise Cosine Similarity Matrix
        matrix = self._compute_similarity_matrix(embeddings)

        # 2. Compute mean intra-sample similarity for each embedding (excluding self-similarity)
        intra_scores = []
        for i in range(n):
            other_sims = [matrix[i][j] for j in range(n) if i != j]
            intra_scores.append(float(np.mean(other_sims)))

        mean_all = float(np.mean(intra_scores))
        std_all = float(np.std(intra_scores)) if n > 2 else 0.0

        accepted: List[int] = []
        rejected: List[int] = []
        reasons: Dict[int, str] = {}

        for i, score in enumerate(intra_scores):
            # Check absolute threshold
            if score < self.min_intra_similarity:
                rejected.append(i)
                reasons[i] = f"Intra-identity similarity {score:.3f} below minimum {self.min_intra_similarity:.2f}"
                continue

            # Check statistical deviation (lower outlier)
            if std_all > 0.05 and score < (mean_all - self.sigma_threshold * std_all):
                rejected.append(i)
                reasons[i] = f"Statistical outlier: similarity {score:.3f} is > {self.sigma_threshold}σ below mean ({mean_all:.3f})"
                continue

            accepted.append(i)

        # If too many were rejected (safety guard), retain the highest-scoring core
        if len(accepted) < 2 and n >= 2:
            sorted_by_score = sorted(range(n), key=lambda idx: intra_scores[idx], reverse=True)
            accepted = sorted_by_score[:max(2, n // 2)]
            rejected = [i for i in range(n) if i not in accepted]

        accepted_matrix_sims = [
            matrix[i][j] for i in accepted for j in accepted if i != j
        ]
        mean_accepted_sim = float(np.mean(accepted_matrix_sims)) if accepted_matrix_sims else 1.0

        return OutlierFilterResult(
            accepted_indices=accepted,
            rejected_indices=rejected,
            pairwise_matrix=matrix.tolist(),
            mean_intra_similarity=mean_accepted_sim,
            rejection_reasons=reasons
        )

    def _compute_similarity_matrix(self, embeddings: List[np.ndarray]) -> np.ndarray:
        stack = np.array(embeddings, dtype=np.float32)
        # Ensure L2 normalized
        norms = np.linalg.norm(stack, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = stack / norms
        # Dot product of unit vectors equals cosine similarity
        return np.dot(normalized, normalized.T)
