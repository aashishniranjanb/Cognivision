"""FAISS Index Manager: Rebuilds, serializes, and hot-reloads the FAISS Vector Search Index from SQLite Biometric Database."""
import faiss
import numpy as np
import pickle
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from app.biometrics.repository import BiometricRepository

@dataclass
class IndexedVectorMeta:
    vector_id: int
    student_id: str
    vector_type: str  # "CANONICAL" or "VARIANT"
    variant_id: Optional[int] = None
    pose_type: str = "FRONTAL"
    quality_score: float = 1.0

@dataclass
class IndexStats:
    total_vectors: int
    total_students: int
    dimension: int
    index_file: str
    last_rebuilt: str
    canonical_count: int
    variant_count: int

def _resolve_path(rel_path: str = "data/face_embeddings") -> Path:
    p = Path(rel_path)
    if p.is_absolute():
        return p
    here = Path(__file__).resolve()
    ai_root = here.parent.parent.parent
    return ai_root / rel_path

class FaissIndexManager:
    def __init__(
        self,
        repo: Optional[BiometricRepository] = None,
        index_dir: str = "data/face_embeddings",
        dim: int = 512,
        include_variants: bool = True
    ):
        self.dim = dim
        self.include_variants = include_variants
        self.repo = repo or BiometricRepository()
        self.storage_dir = _resolve_path(index_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.storage_dir / "face_index.faiss"
        self.mapping_file = self.storage_dir / "id_mapping.pkl"
        self.metadata_file = self.storage_dir / "vector_metadata.pkl"

        self.index = faiss.IndexFlatIP(self.dim)
        self.id_mapping: List[str] = []
        self.metadata: List[IndexedVectorMeta] = []
        self.last_rebuilt: Optional[str] = None

        self.load()

    def rebuild_index(self) -> IndexStats:
        """Rebuilds the entire FAISS index from scratch using all READY profiles and variants in SQLite."""
        new_index = faiss.IndexFlatIP(self.dim)
        new_id_mapping: List[str] = []
        new_metadata: List[IndexedVectorMeta] = []

        all_students = self.repo.list_students(limit=10000)
        canonical_count = 0
        variant_count = 0
        vectors_to_add: List[np.ndarray] = []

        for student in all_students:
            profile = self.repo.get_biometric_profile(student.student_id)
            if not profile or profile.status != "READY" or not profile.has_template:
                continue

            # 1. Add Canonical Template
            template_vec = self.repo.get_template_embedding(student.student_id)
            if template_vec and len(template_vec) == self.dim:
                arr = np.array(template_vec, dtype=np.float32)
                norm = np.linalg.norm(arr)
                if norm > 1e-6:
                    arr = arr / norm
                vectors_to_add.append(arr)

                vid = len(new_id_mapping)
                new_id_mapping.append(student.student_id)
                new_metadata.append(IndexedVectorMeta(
                    vector_id=vid,
                    student_id=student.student_id,
                    vector_type="CANONICAL",
                    pose_type="FRONTAL",
                    quality_score=profile.enrollment_quality
                ))
                canonical_count += 1

            # 2. Add Variants if configured
            if self.include_variants:
                variants = self.repo.get_variant_embeddings(student.student_id)
                for var_id, var_vec, pose, qual in variants:
                    if len(var_vec) == self.dim:
                        var_arr = np.array(var_vec, dtype=np.float32)
                        vnorm = np.linalg.norm(var_arr)
                        if vnorm > 1e-6:
                            var_arr = var_arr / vnorm
                        vectors_to_add.append(var_arr)

                        vid = len(new_id_mapping)
                        new_id_mapping.append(student.student_id)
                        new_metadata.append(IndexedVectorMeta(
                            vector_id=vid,
                            student_id=student.student_id,
                            vector_type="VARIANT",
                            variant_id=var_id,
                            pose_type=pose,
                            quality_score=qual
                        ))
                        variant_count += 1

        if vectors_to_add:
            matrix = np.ascontiguousarray(np.stack(vectors_to_add), dtype=np.float32)
            new_index.add(matrix)

        # Atomic swap in memory
        self.index = new_index
        self.id_mapping = new_id_mapping
        self.metadata = new_metadata
        self.last_rebuilt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Persist to disk
        self.save()

        unique_students = len(set(new_id_mapping))
        return IndexStats(
            total_vectors=self.index.ntotal,
            total_students=unique_students,
            dimension=self.dim,
            index_file=str(self.index_file),
            last_rebuilt=self.last_rebuilt,
            canonical_count=canonical_count,
            variant_count=variant_count
        )

    def save(self):
        faiss.write_index(self.index, str(self.index_file))
        with open(self.mapping_file, "wb") as f:
            pickle.dump(self.id_mapping, f)
        with open(self.metadata_file, "wb") as f:
            pickle.dump(self.metadata, f)

    def load(self):
        if self.index_file.exists() and self.mapping_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.mapping_file, "rb") as f:
                    self.id_mapping = pickle.load(f)
                if self.metadata_file.exists():
                    with open(self.metadata_file, "rb") as f:
                        self.metadata = pickle.load(f)
                self.last_rebuilt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            except Exception as e:
                print(f"[FaissIndexManager] Warning loading index: {e}")
                self.index = faiss.IndexFlatIP(self.dim)
                self.id_mapping = []
                self.metadata = []

    def get_stats(self) -> IndexStats:
        unique_students = len(set(self.id_mapping))
        canonical = sum(1 for m in self.metadata if m.vector_type == "CANONICAL")
        variants = sum(1 for m in self.metadata if m.vector_type == "VARIANT")
        return IndexStats(
            total_vectors=self.index.ntotal,
            total_students=unique_students,
            dimension=self.dim,
            index_file=str(self.index_file),
            last_rebuilt=self.last_rebuilt or "Never",
            canonical_count=canonical,
            variant_count=variants
        )
