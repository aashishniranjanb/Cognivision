"""Unit and Integration Tests for V1.3 Sprint A — Biometric Database & CRUD APIs."""
import pytest
import tempfile
import os
import json
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from app.biometrics.database import BiometricDatabase
from app.biometrics.repository import BiometricRepository
from app.biometrics.schemas import (
    StudentCreate, StudentUpdate, EmbeddingVariantCreate,
    serialize_embedding, deserialize_embedding
)
from app.biometrics.migration import run_migration
from app.backend.api import app

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = BiometricDatabase(db_path=db_path)
    yield db
    try:
        os.remove(db_path)
    except OSError:
        pass

@pytest.fixture
def repo(temp_db):
    return BiometricRepository(db=temp_db)

class TestBiometricDatabaseCRUD:
    def test_student_crud(self, repo):
        # 1. Create Student
        s_in = StudentCreate(
            student_id="STU999",
            register_number="RA2311003010999",
            name="Test Candidate",
            department="ECE",
            year=4,
            section="B",
            status="ACTIVE"
        )
        created = repo.create_student(s_in)
        assert created.student_id == "STU999"
        assert created.name == "Test Candidate"
        assert created.biometric_status == "PENDING"
        assert created.enrolled_images == 0

        # 2. Get Student
        fetched = repo.get_student("STU999")
        assert fetched is not None
        assert fetched.register_number == "RA2311003010999"

        # 3. Update Student
        up = StudentUpdate(name="Test Candidate Updated", section="C")
        updated = repo.update_student("STU999", up)
        assert updated.name == "Test Candidate Updated"
        assert updated.section == "C"

        # 4. List Students
        all_students = repo.list_students(search="Candidate", department="ECE")
        assert len(all_students) == 1
        assert all_students[0].student_id == "STU999"

        # 5. Delete Student
        deleted = repo.delete_student("STU999")
        assert deleted is True
        assert repo.get_student("STU999") is None

    def test_biometric_profile_and_serialization(self, repo):
        # Create student first
        s_in = StudentCreate(
            student_id="STU888",
            register_number="RA2311003010888",
            name="Vector Test",
            department="CSE",
            year=3
        )
        repo.create_student(s_in)

        # Generate fake 512-D normalized vector
        vec = np.random.randn(512).astype(np.float32)
        vec /= np.linalg.norm(vec)
        vec_list = vec.tolist()

        # Test raw byte serialization
        raw_bytes = serialize_embedding(vec_list)
        deserialized = deserialize_embedding(raw_bytes)
        assert len(deserialized) == 512
        np.testing.assert_allclose(vec_list, deserialized, atol=1e-5)

        # Upsert profile with template vector
        profile = repo.upsert_biometric_profile(
            student_id="STU888",
            template_embedding=vec_list,
            template_version=2,
            enrollment_quality=0.92,
            enrolled_images=5,
            status="READY"
        )
        assert profile.status == "READY"
        assert profile.template_version == 2
        assert profile.has_template is True

        retrieved_template = repo.get_template_embedding("STU888")
        assert retrieved_template is not None
        np.testing.assert_allclose(vec_list, retrieved_template, atol=1e-5)

    def test_embedding_variants_crud(self, repo):
        s_in = StudentCreate(
            student_id="STU777",
            register_number="RA2311003010777",
            name="Variant Multi",
            department="ECE",
            year=4
        )
        repo.create_student(s_in)

        # Add 3 variants with different qualities and poses
        v1 = EmbeddingVariantCreate(
            embedding=np.random.randn(512).tolist(),
            face_width=112.0,
            blur_score=156.4,
            illumination_score=0.85,
            yaw=5.0,
            pitch=2.0,
            roll=0.5,
            detection_confidence=0.98,
            quality_score=0.94,
            source_image="captures/stu777_v1.jpg"
        )
        v2 = EmbeddingVariantCreate(
            embedding=np.random.randn(512).tolist(),
            face_width=98.0,
            blur_score=132.0,
            illumination_score=0.78,
            yaw=-15.0,
            pitch=-4.0,
            roll=-1.0,
            detection_confidence=0.95,
            quality_score=0.88,
            source_image="captures/stu777_v2.jpg"
        )
        v3 = EmbeddingVariantCreate(
            embedding=np.random.randn(512).tolist(),
            face_width=84.0,
            blur_score=110.0,
            illumination_score=0.72,
            yaw=20.0,
            pitch=6.0,
            roll=2.0,
            detection_confidence=0.92,
            quality_score=0.82,
            source_image="captures/stu777_v3.jpg"
        )

        res1 = repo.add_variant("STU777", v1)
        res2 = repo.add_variant("STU777", v2)
        res3 = repo.add_variant("STU777", v3)

        assert res1.id is not None
        assert res2.id is not None

        # Check variants list sorted by quality
        variants = repo.list_variants("STU777")
        assert len(variants) == 3
        assert variants[0].quality_score >= variants[1].quality_score >= variants[2].quality_score

        # Check detail response aggregation
        detail = repo.get_student_detail("STU777")
        assert detail is not None
        assert detail.enrolled_images == 3
        assert len(detail.variants) == 3

        # Delete 1 variant
        del_ok = repo.delete_variant(res2.id)
        assert del_ok is True
        variants_after = repo.list_variants("STU777")
        assert len(variants_after) == 2

    def test_migration_utility(self):
        # Create a mock legacy registry JSON
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as jf:
            json.dump({
                "MIG001": {"student_id": "MIG001", "name": "Migrated One", "department": "ECE", "year": 4, "active": True, "embedding_count": 4},
                "MIG002": {"student_id": "MIG002", "name": "Migrated Two", "department": "CSE", "year": 3, "active": True, "embedding_count": 0}
            }, jf)
            json_file = jf.name

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as df:
            db_file = df.name

        try:
            report = run_migration(json_path=json_file, db_path=db_file)
            assert report["status"] == "success"
            assert report["migrated"] == 2
            assert report["skipped"] == 0

            # Re-run migration: should skip all 2
            report_rerun = run_migration(json_path=json_file, db_path=db_file)
            assert report_rerun["migrated"] == 0
            assert report_rerun["skipped"] == 2

            # Verify contents
            db = BiometricDatabase(db_path=db_file)
            repo = BiometricRepository(db=db)
            s1 = repo.get_student("MIG001")
            assert s1 is not None
            assert s1.biometric_status == "READY"
            s2 = repo.get_student("MIG002")
            assert s2 is not None
            assert s2.biometric_status == "PENDING"
        finally:
            try:
                os.remove(json_file)
            except OSError:
                pass
            try:
                os.remove(db_file)
            except OSError:
                pass

class TestBiometricAPIEndpoints:
    def test_api_student_lifecycle(self):
        client = TestClient(app)

        # 1. Create Student
        res = client.post("/api/students", json={
            "student_id": "API_STU01",
            "register_number": "RA23API001",
            "name": "API Student Alpha",
            "department": "ECE",
            "year": 4,
            "section": "A",
            "status": "ACTIVE"
        })
        assert res.status_code == 201
        data = res.json()
        assert data["student_id"] == "API_STU01"

        # 2. Duplicate rejection
        dup = client.post("/api/students", json={
            "student_id": "API_STU01",
            "name": "Duplicate",
            "department": "ECE",
            "year": 4
        })
        assert dup.status_code == 400

        # 3. List Students
        list_res = client.get("/api/students?search=API%20Student")
        assert list_res.status_code == 200
        items = list_res.json()
        assert any(i["student_id"] == "API_STU01" for i in items)

        # 4. Add Variant
        v_res = client.post("/api/students/API_STU01/variants", json={
            "embedding": [0.05] * 512,
            "face_width": 105.0,
            "blur_score": 145.0,
            "illumination_score": 0.88,
            "yaw": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "detection_confidence": 0.99,
            "quality_score": 0.95
        })
        assert v_res.status_code == 201
        var_data = v_res.json()
        variant_id = var_data["id"]

        # 5. Detail View
        detail_res = client.get("/api/students/API_STU01/detail")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["student_id"] == "API_STU01"
        # 6. Delete Variant
        del_v = client.delete(f"/api/students/API_STU01/variants/{variant_id}")
        assert del_v.status_code == 200

        # 7. Delete Student
        del_s = client.delete("/api/students/API_STU01")
        assert del_s.status_code == 200
        assert client.get("/api/students/API_STU01/detail").status_code == 404

    def test_foreign_key_cascades_and_constraints(self, repo):
        # Test cascade delete: deleting student deletes profile and all variants
        s_in = StudentCreate(
            student_id="CASCADE_01",
            name="Cascade Tester",
            department="CSE",
            year=2
        )
        repo.create_student(s_in)
        repo.add_variant("CASCADE_01", EmbeddingVariantCreate(
            embedding=[0.1] * 512,
            quality_score=0.9
        ))
        repo.add_variant("CASCADE_01", EmbeddingVariantCreate(
            embedding=[0.2] * 512,
            quality_score=0.85
        ))
        assert len(repo.list_variants("CASCADE_01")) == 2

        # Delete student
        assert repo.delete_student("CASCADE_01") is True
        # Verify variants and profile are cascade-deleted
        assert len(repo.list_variants("CASCADE_01")) == 0
        assert repo.get_biometric_profile("CASCADE_01") is None

    def test_large_roster_stress_and_filtering(self, repo):
        # Stress test: batch create 100 students across departments
        departments = ["ECE", "CSE", "MECH", "IT", "EEE"]
        for i in range(100):
            sid = f"STU_BATCH_{i:03d}"
            dept = departments[i % len(departments)]
            yr = (i % 4) + 1
            repo.create_student(StudentCreate(
                student_id=sid,
                name=f"Student {i:03d}",
                department=dept,
                year=yr,
                status="ACTIVE" if i % 10 != 0 else "INACTIVE"
            ))

        # Test filtering permutations
        ece_year4 = repo.list_students(department="ECE", year=4, limit=100)
        assert len(ece_year4) > 0
        assert all(s.department == "ECE" and s.year == 4 for s in ece_year4)

        inactive_students = repo.list_students(status="INACTIVE", limit=100)
        assert len(inactive_students) == 10

        search_results = repo.list_students(search="042", limit=10)
        assert len(search_results) == 1
        assert search_results[0].student_id == "STU_BATCH_042"

