"""FAISS Candidate Retrieval: High-speed top-K candidate search without making premature identity decisions."""
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from app.face.index_manager import FaissIndexManager, IndexedVectorMeta

@dataclass
class VectorHit:
    student_id: str
    similarity: float
    vector_id: int
    vector_type: str
    pose_type: str
    quality_score: float

@dataclass
class RetrievedCandidate:
    student_id: str
    rank: int
    max_similarity: float
    canonical_similarity: Optional[float]
    best_variant_similarity: Optional[float]
    best_matching_pose: str
    hit_count: int
    vector_hits: List[VectorHit] = field(default_factory=list)

class FaissCandidateRetriever:
    def __init__(self, index_manager: FaissIndexManager, default_top_k: int = 10):
        self.index_manager = index_manager
        self.default_top_k = default_top_k

    def retrieve_candidates(
        self,
        query_embedding: np.ndarray,
        top_k: Optional[int] = None
    ) -> List[RetrievedCandidate]:
        """Retrieves top-K candidate students from the FAISS vector index."""
        if self.index_manager.index.ntotal == 0:
            return []

        k = min(top_k or self.default_top_k, self.index_manager.index.ntotal)
        arr = np.ascontiguousarray(query_embedding.reshape(1, -1), dtype=np.float32)

        # Ensure query is L2 normalized
        norm = np.linalg.norm(arr)
        if norm > 1e-6:
            arr = arr / norm

        scores, indices = self.index_manager.index.search(arr, k)

        # Group hits by student_id
        candidate_groups: Dict[str, List[VectorHit]] = {}

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.index_manager.id_mapping):
                continue

            sid = self.index_manager.id_mapping[idx]
            meta = self.index_manager.metadata[idx] if idx < len(self.index_manager.metadata) else None

            hit = VectorHit(
                student_id=sid,
                similarity=float(score),
                vector_id=int(idx),
                vector_type=meta.vector_type if meta else "UNKNOWN",
                pose_type=meta.pose_type if meta else "FRONTAL",
                quality_score=meta.quality_score if meta else 1.0
            )

            if sid not in candidate_groups:
                candidate_groups[sid] = []
            candidate_groups[sid].append(hit)

        # Aggregate metrics for each candidate student
        aggregated: List[RetrievedCandidate] = []
        for sid, hits in candidate_groups.items():
            max_sim = max(h.similarity for h in hits)
            best_hit = max(hits, key=lambda h: h.similarity)

            can_hits = [h.similarity for h in hits if h.vector_type == "CANONICAL"]
            var_hits = [h.similarity for h in hits if h.vector_type == "VARIANT"]

            can_sim = can_hits[0] if can_hits else None
            var_sim = max(var_hits) if var_hits else None

            aggregated.append(RetrievedCandidate(
                student_id=sid,
                rank=0,  # Will assign after sort
                max_similarity=round(max_sim, 4),
                canonical_similarity=round(can_sim, 4) if can_sim is not None else None,
                best_variant_similarity=round(var_sim, 4) if var_sim is not None else None,
                best_matching_pose=best_hit.pose_type,
                hit_count=len(hits),
                vector_hits=hits
            ))

        # Sort descending by max similarity
        aggregated.sort(key=lambda c: c.max_similarity, reverse=True)
        for i, c in enumerate(aggregated):
            c.rank = i + 1

        return aggregated
