"""FAISS Vector Index & Candidate Matcher for high-speed student identity search."""
import faiss
import numpy as np
import os
import pickle
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class MatchResult:
    student_id: str
    similarity: float          # Cosine similarity (-1.0 to 1.0, typical 0.0 to 1.0)
    matched_vector_idx: int

def _resolve_path(rel_path: str) -> Path:
    p = Path(rel_path)
    if p.is_absolute():
        return p
    here = Path(__file__).resolve()
    candidates = [
        p,
        here.parent.parent.parent.parent / rel_path,
        here.parent.parent.parent / rel_path,
        here.parent.parent / rel_path,
    ]
    for c in candidates:
        if c.exists():
            return c
    return here.parent.parent.parent.parent / rel_path

class FaceMatcher:
    def __init__(self, index_file: str = "data/face_embeddings/face_index.faiss", mapping_file: str = "data/face_embeddings/id_mapping.pkl", dim: int = 512):
        self.dim = dim
        self.index_file = _resolve_path(index_file)
        self.mapping_file = _resolve_path(mapping_file)
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Inner-Product Index (exact cosine similarity when vectors are L2-normalized)
        self.index = faiss.IndexFlatIP(self.dim)
        self.id_mapping: List[str] = []  # Index i -> student_id
        self.load()

    def add_embedding(self, student_id: str, embedding: np.ndarray):
        """Adds a normalized 512-d embedding linked to a student_id."""
        vec = np.ascontiguousarray(embedding.reshape(1, -1), dtype=np.float32)
        self.index.add(vec)
        self.id_mapping.append(student_id)
        self.save()

    def search(self, query_embedding: np.ndarray, top_k: int = 1) -> List[MatchResult]:
        """Finds top-k most similar registered student candidates."""
        if self.index.ntotal == 0:
            return []

        query = np.ascontiguousarray(query_embedding.reshape(1, -1), dtype=np.float32)
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.id_mapping):
                results.append(MatchResult(
                    student_id=self.id_mapping[idx],
                    similarity=float(score),
                    matched_vector_idx=int(idx)
                ))
        return results

    def save(self):
        faiss.write_index(self.index, str(self.index_file))
        with open(self.mapping_file, "wb") as f:
            pickle.dump(self.id_mapping, f)

    def load(self):
        if self.index_file.exists() and self.mapping_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.mapping_file, "rb") as f:
                    self.id_mapping = pickle.load(f)
                print(f"[FaceMatcher] Loaded FAISS index with {self.index.ntotal} registered face vectors.")
            except Exception as e:
                print(f"[FaceMatcher] Warning: Failed to load index: {e}")
                self.index = faiss.IndexFlatIP(self.dim)
                self.id_mapping = []
