"""Unit and Integration Tests for V1.3 Batch 4 (Tasks 16 to 20):
Variant Storage, Template Versioning, FAISS Rebuild, Candidate Retrieval, and Verification.
"""
import pytest
import numpy as np
import tempfile
import os
from fastapi.testclient import TestClient

from app.biometrics.database import BiometricDatabase
from app.biometrics.repository import BiometricRepository
from app.biometrics.schemas import StudentCreate, EmbeddingVariantCreate
from app.face.index_manager import FaissIndexManager
from app.face.candidate_retriever import FaissCandidateRetriever
from app.face.candidate_verifier import CandidateVerifier
from app.backend.api import app

import shutil

@pytest.fixture
def isolated_env():
    td = tempfile.mkdtemp()
    db_file = os.path.join(td, "test_bio.db")
    db = BiometricDatabase(db_path=db_file)
    repo = BiometricRepository(db=db)
    index_dir = os.path.join(td, "faiss_index")
    idx_mgr = FaissIndexManager(repo=repo, index_dir=index_dir)
    retriever = FaissCandidateRetriever(index_manager=idx_mgr)
    verifier = CandidateVerifier(biometric_repo=repo)
    yield {
        "db": db,
        "repo": repo,
        "idx_mgr": idx_mgr,
        "retriever": retriever,
        "verifier": verifier
    }
    shutil.rmtree(td, ignore_errors=True)

def make_unit_vec(dim=512, seed=None):
    if seed is not None:
        np.random.seed(seed)
    v = np.random.randn(dim).astype(np.float32)
    return (v / np.linalg.norm(v)).tolist()

class TestTask16VariantStorageAndTask17Versioning:
    def test_variant_pose_storage(self, isolated_env):
        repo = isolated_env["repo"]
        repo.create_student(StudentCreate(
            student_id="VAR_STU01",
            name="Variant Student",
            department="ECE",
            year=4
        ))

        # Add 3 variants with different pose types
        repo.add_variant("VAR_STU01", EmbeddingVariantCreate(
            embedding=make_unit_vec(seed=1),
            pose_type="FRONTAL",
            quality_score=0.95
        ))
        repo.add_variant("VAR_STU01", EmbeddingVariantCreate(
            embedding=make_unit_vec(seed=2),
            pose_type="LEFT_PROFILE",
            quality_score=0.88
        ))
        repo.add_variant("VAR_STU01", EmbeddingVariantCreate(
            embedding=make_unit_vec(seed=3),
            pose_type="RIGHT_PROFILE",
            quality_score=0.86
        ))

        variants = repo.list_variants("VAR_STU01")
        assert len(variants) == 3
        poses = {v.pose_type for v in variants}
        assert "FRONTAL" in poses
        assert "LEFT_PROFILE" in poses
        assert "RIGHT_PROFILE" in poses

    def test_template_versioning_and_rollback(self, isolated_env):
        repo = isolated_env["repo"]
        repo.create_student(StudentCreate(
            student_id="VER_STU01",
            name="Version Student",
            department="CSE",
            year=3
        ))

        # Version 1 initial template
        t1 = make_unit_vec(seed=10)
        repo.upsert_biometric_profile(
            student_id="VER_STU01",
            template_embedding=t1,
            enrollment_quality=0.85,
            status="READY"
        )
        p1 = repo.get_biometric_profile("VER_STU01")
        assert p1.template_version == 1

        # Version 2 re-enrollment
        t2 = make_unit_vec(seed=20)
        repo.upsert_biometric_profile(
            student_id="VER_STU01",
            template_embedding=t2,
            enrollment_quality=0.94,
            status="READY",
            archive_notes="Re-enrollment with updated cameras"
        )
        p2 = repo.get_biometric_profile("VER_STU01")
        assert p2.template_version == 2

        # Check history has version 1 archived
        history = repo.get_template_history("VER_STU01")
        assert len(history) == 1
        assert history[0].template_version == 1

        # Rollback to version 1
        rolled = repo.rollback_template("VER_STU01", target_version=1)
        assert rolled is not None
        assert rolled.template_version == 1
        current_t = repo.get_template_embedding("VER_STU01")
        np.testing.assert_allclose(current_t, t1, atol=1e-5)

class TestTask18FaissRebuild:
    def test_rebuild_from_database(self, isolated_env):
        repo = isolated_env["repo"]
        idx_mgr = isolated_env["idx_mgr"]

        # Register 3 students with templates and variants
        for i in range(3):
            sid = f"FAISS_STU_{i+1:02d}"
            repo.create_student(StudentCreate(student_id=sid, name=f"Student {i+1}", department="ECE", year=4))
            repo.upsert_biometric_profile(
                student_id=sid,
                template_embedding=make_unit_vec(seed=100 + i),
                status="READY",
                enrollment_quality=0.9
            )
            # Add 2 variants each
            repo.add_variant(sid, EmbeddingVariantCreate(
                embedding=make_unit_vec(seed=200 + i*2),
                pose_type="FRONTAL",
                quality_score=0.92
            ))
            repo.add_variant(sid, EmbeddingVariantCreate(
                embedding=make_unit_vec(seed=201 + i*2),
                pose_type="LEFT_PROFILE",
                quality_score=0.88
            ))

        stats = idx_mgr.rebuild_index()
        assert stats.total_students == 3
        # 3 canonicals + 6 variants = 9 total vectors
        assert stats.canonical_count == 3
        assert stats.variant_count == 6
        assert stats.total_vectors == 9
        assert idx_mgr.index.ntotal == 9

class TestTask19RetrievalAndTask20Verification:
    def test_candidate_retrieval_and_verified_match(self, isolated_env):
        repo = isolated_env["repo"]
        idx_mgr = isolated_env["idx_mgr"]
        retriever = isolated_env["retriever"]
        verifier = isolated_env["verifier"]

        # Register target student
        sid = "VERIFY_TARGET"
        repo.create_student(StudentCreate(student_id=sid, name="Target Candidate", department="ECE", year=4))

        base_t = np.array(make_unit_vec(seed=42), dtype=np.float32)
        repo.upsert_biometric_profile(
            student_id=sid,
            template_embedding=base_t.tolist(),
            status="READY",
            enrollment_quality=0.95
        )
        # Left profile variant correlated with base_t
        noise = np.random.randn(512).astype(np.float32)
        noise /= np.linalg.norm(noise)
        left_v = 0.88 * base_t + 0.12 * noise
        left_v /= np.linalg.norm(left_v)

        repo.add_variant(sid, EmbeddingVariantCreate(
            embedding=left_v.tolist(),
            pose_type="LEFT_PROFILE",
            quality_score=0.90
        ))

        idx_mgr.rebuild_index()

        # 1. Frontal Query with mild noise -> Should verify as MATCH
        noisy_query = base_t + np.random.randn(512).astype(np.float32) * 0.05
        noisy_query /= np.linalg.norm(noisy_query)

        candidates = retriever.retrieve_candidates(noisy_query, top_k=5)
        assert len(candidates) >= 1
        assert candidates[0].student_id == sid

        decision = verifier.verify_candidates(noisy_query, candidates, query_yaw=0.0)
        assert decision.is_verified is True
        assert decision.decision == "VERIFIED_MATCH"
        assert decision.student_id == sid
        assert decision.composite_similarity >= 0.68

    def test_unknown_rejection(self, isolated_env):
        idx_mgr = isolated_env["idx_mgr"]
        retriever = isolated_env["retriever"]
        verifier = isolated_env["verifier"]

        # Orthogonal random vector that doesn't match any enrolled student
        unknown_query = np.array(make_unit_vec(seed=9999), dtype=np.float32)
        candidates = retriever.retrieve_candidates(unknown_query, top_k=5)
        decision = verifier.verify_candidates(unknown_query, candidates)

        assert decision.is_verified is False
        assert decision.decision == "UNKNOWN_REJECTED"
        assert decision.student_id is None

class TestRecognitionAPIRoutes:
    def test_index_and_verify_endpoints(self):
        client = TestClient(app)

        # 1. Stats Endpoint
        stats_res = client.get("/api/biometrics/index/stats")
        assert stats_res.status_code == 200
        stats_data = stats_res.json()
        assert "total_vectors" in stats_data
        assert "dimension" in stats_data

        # 2. Rebuild Endpoint
        rebuild_res = client.post("/api/biometrics/index/rebuild")
        assert rebuild_res.status_code == 200
        rebuild_data = rebuild_res.json()
        assert "total_vectors" in rebuild_data

        # 3. Verify Endpoint
        test_vec = make_unit_vec(seed=55)
        verify_res = client.post("/api/biometrics/verify", json={
            "embedding": test_vec,
            "query_yaw": 0.0,
            "top_k": 3
        })
        assert verify_res.status_code == 200
        v_data = verify_res.json()
        assert "decision" in v_data
        assert "composite_similarity" in v_data
