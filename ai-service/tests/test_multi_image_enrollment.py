"""Unit and Integration Tests for V1.3 Batch 3 (Tasks 11 to 15):
Quality Gate, ArcFace Embedder, Outlier Rejection, Centroid Aggregation, and Multi-Image Enrollment.
"""
import pytest
import numpy as np
import cv2
import tempfile
import os
from fastapi.testclient import TestClient

from app.face.quality_gate import EnrollmentQualityGate, QualityGateResult
from app.face.arcface_embedder import ArcFaceEmbeddingService
from app.face.outlier_rejection import EmbeddingOutlierFilter, OutlierFilterResult
from app.face.template_aggregator import TemplateAggregator, AggregatedTemplateResult
from app.enrollment.multi_image_enrollment import MultiImageEnrollmentEngine
from app.biometrics.database import BiometricDatabase
from app.biometrics.repository import BiometricRepository
from app.biometrics.schemas import StudentCreate
from app.backend.api import app

def generate_test_face(w=140, h=140, blurred=False, low_res=False):
    """Generates synthetic face image with clear geometric features."""
    if low_res:
        w, h = 50, 50
    img = np.ones((h, w, 3), dtype=np.uint8) * 200
    cv2.ellipse(img, (w // 2, h // 2), (w // 3, h // 2 - 10), 0, 0, 360, (160, 140, 120), -1)
    cv2.circle(img, (w // 2 - 20, h // 2 - 15), 5, (20, 20, 20), -1)
    cv2.circle(img, (w // 2 + 20, h // 2 - 15), 5, (20, 20, 20), -1)
    cv2.line(img, (w // 2, h // 2 - 5), (w // 2, h // 2 + 10), (50, 50, 50), 2)
    cv2.ellipse(img, (w // 2, h // 2 + 25), (15, 6), 0, 0, 180, (20, 20, 150), 2)
    if blurred:
        img = cv2.GaussianBlur(img, (21, 21), 10)
    return img

@pytest.fixture
def temp_repo():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = BiometricDatabase(db_path=db_path)
    repo = BiometricRepository(db=db)
    yield repo
    try:
        os.remove(db_path)
    except OSError:
        pass

class TestTask11QualityGate:
    def test_gate_accepts_good_face(self):
        gate = EnrollmentQualityGate(min_face_width=70.0, min_blur_score=80.0)
        face = generate_test_face(w=140, h=140)
        res = gate.process_frame(face)
        assert res.passed is True
        assert res.aligned_face is not None
        assert res.aligned_face.shape == (112, 112, 3)

    def test_gate_rejects_blurred_face(self):
        gate = EnrollmentQualityGate(min_blur_score=100.0)
        face_blurred = generate_test_face(w=140, h=140, blurred=True)
        res = gate.process_frame(face_blurred)
        assert res.passed is False
        assert len(res.failure_reasons) > 0

class TestTask12ArcFaceEmbedder:
    def test_embedding_dimensions_and_l2_norm(self):
        embedder = ArcFaceEmbeddingService(embedding_dim=512)
        face = generate_test_face(w=112, h=112)
        emb = embedder.extract(face)
        assert emb.shape == (512,)
        assert emb.dtype == np.float32
        norm = np.linalg.norm(emb)
        assert pytest.approx(norm, abs=1e-4) == 1.0

    def test_batch_extraction(self):
        embedder = ArcFaceEmbeddingService(embedding_dim=512)
        batch = [generate_test_face(w=112, h=112) for _ in range(4)]
        embeddings = embedder.extract_batch(batch)
        assert len(embeddings) == 4
        for emb in embeddings:
            assert emb.shape == (512,)
            assert pytest.approx(np.linalg.norm(emb), abs=1e-4) == 1.0

class TestTask14OutlierRejection:
    def test_outlier_filtering(self):
        # Create a cluster of 5 similar vectors (cosine sim ~0.90) and 1 distinct vector
        base = np.random.randn(512).astype(np.float32)
        base /= np.linalg.norm(base)

        cluster = []
        for _ in range(5):
            noise = np.random.randn(512).astype(np.float32)
            noise /= np.linalg.norm(noise)
            vec = 0.92 * base + 0.08 * noise
            vec /= np.linalg.norm(vec)
            cluster.append(vec)

        # Outlier vector (orthogonal / opposite)
        outlier = -base
        cluster.append(outlier)

        filter_engine = EmbeddingOutlierFilter(min_intra_similarity=0.40)
        res = filter_engine.filter_outliers(cluster)

        # Index 5 (outlier) should be rejected
        assert 5 in res.rejected_indices
        assert len(res.accepted_indices) == 5
        assert res.mean_intra_similarity > 0.70

class TestTask15TemplateAggregator:
    def test_quality_weighted_centroid(self):
        aggregator = TemplateAggregator(embedding_dim=512)
        # Create 3 vectors
        v1 = np.array([1.0] + [0.0] * 511, dtype=np.float32)
        v2 = np.array([0.8, 0.6] + [0.0] * 510, dtype=np.float32)
        v3 = np.array([0.9, 0.1] + [0.0] * 510, dtype=np.float32)
        v3 /= np.linalg.norm(v3)

        qualities = [0.95, 0.60, 0.85]
        res = aggregator.aggregate([v1, v2, v3], quality_scores=qualities)

        assert res.canonical_embedding.shape == (512,)
        assert pytest.approx(np.linalg.norm(res.canonical_embedding), abs=1e-4) == 1.0
        assert res.enrolled_count == 3
        assert res.intra_class_compactness > 0.80

class TestTask13MultiImageEnrollmentEngine:
    def test_full_pipeline_multi_image_enrollment(self, temp_repo):
        engine = MultiImageEnrollmentEngine(
            min_required_variants=3,
            biometric_repo=temp_repo
        )

        # Create student in repo
        temp_repo.create_student(StudentCreate(
            student_id="STU_ENG_01",
            name="Engine Test Student",
            department="ECE",
            year=4
        ))

        # Generate 5 test frames: 4 valid + 1 blurred
        frames = [
            generate_test_face(w=140, h=140) for _ in range(4)
        ] + [generate_test_face(w=140, h=140, blurred=True)]

        res = engine.enroll_student(
            student_id="STU_ENG_01",
            images=frames,
            save_to_database=True
        )

        assert res.success is True
        assert res.status == "READY"
        assert res.total_images_submitted == 5
        assert res.passed_quality_gate == 4
        assert res.rejected_quality_gate == 1
        assert res.final_variants_count >= 3
        assert res.canonical_embedding is not None

        # Verify database profile was updated to READY
        profile = temp_repo.get_biometric_profile("STU_ENG_01")
        assert profile is not None
        assert profile.status == "READY"
        assert profile.has_template is True

        # Verify variants stored
        variants = temp_repo.list_variants("STU_ENG_01")
        assert len(variants) >= 3

    def test_api_enrollment_endpoint(self):
        client = TestClient(app)

        # Create student via API
        client.post("/api/students", json={
            "student_id": "API_ENROLL_01",
            "name": "API Enroll Candidate",
            "department": "ECE",
            "year": 4
        })

        # Trigger enrollment with synthetic burst capture
        res = client.post("/api/students/API_ENROLL_01/enroll", json={
            "burst_count": 5,
            "camera_source": "offline_mode"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["student_id"] == "API_ENROLL_01"
        assert data["status"] in ["READY", "RE_ENROLL_REQUIRED"]
