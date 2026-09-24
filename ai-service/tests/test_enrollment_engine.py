"""Unit and Integration Tests for V1.3 Sprint B (Tasks 7 to 10) — Enrollment Engine Modules."""
import pytest
import numpy as np
import cv2
import tempfile
import os
from pathlib import Path

from app.enrollment.capture_service import EnrollmentCaptureService, CapturedFrame
from app.face.enrollment_detector import EnrollmentFaceDetector, EnrollmentFace
from app.face.aligner import FaceAligner, ARCFACE_REFERENCE_LANDMARKS
from app.face.quality_evaluator import EnrollmentQualityEvaluator, EnrollmentQualityReport

@pytest.fixture
def capture_service():
    with tempfile.TemporaryDirectory() as td:
        service = EnrollmentCaptureService(base_storage_dir=td)
        yield service

@pytest.fixture
def detector():
    return EnrollmentFaceDetector(min_face_size=(40, 40))

@pytest.fixture
def aligner():
    return FaceAligner(output_size=(112, 112))

@pytest.fixture
def quality_evaluator():
    return EnrollmentQualityEvaluator(
        min_face_width=80.0,
        min_blur_score=100.0,
        min_quality_score=0.65
    )

def create_synthetic_face(w=160, h=160, blurred=False, low_light=False):
    """Creates synthetic face image for testing."""
    face = np.ones((h, w, 3), dtype=np.uint8) * (50 if low_light else 190)
    # Head contour
    cv2.ellipse(face, (w // 2, h // 2), (w // 3, h // 2 - 10), 0, 0, 360, (140, 120, 100), -1)
    # Eyes
    cv2.circle(face, (w // 2 - 25, h // 2 - 15), 6, (30, 20, 10), -1)
    cv2.circle(face, (w // 2 + 25, h // 2 - 15), 6, (30, 20, 10), -1)
    # Nose & Mouth
    cv2.line(face, (w // 2, h // 2 - 5), (w // 2, h // 2 + 15), (70, 50, 30), 2)
    cv2.ellipse(face, (w // 2, h // 2 + 35), (20, 8), 0, 0, 180, (40, 30, 160), 2)

    if blurred:
        face = cv2.GaussianBlur(face, (25, 25), 10)
    return face

class TestEnrollmentCaptureService:
    def test_burst_capture_synthetic_fallback(self, capture_service):
        frames = capture_service.burst_capture(
            source="invalid_cam_stream",
            student_id="STU_TEST_01",
            count=5,
            interval_ms=10
        )
        assert len(frames) == 5
        assert all(f.image.shape == (480, 640, 3) for f in frames)
        assert all(f.file_path is not None for f in frames)
        assert all(Path(f.file_path).exists() for f in frames)

    def test_guided_pose_capture(self, capture_service):
        poses = ["FRONTAL", "SLIGHT_LEFT", "SLIGHT_RIGHT"]
        frames = capture_service.guided_pose_capture(
            student_id="STU_TEST_02",
            pose_sequence=poses,
            source="invalid_cam"
        )
        assert len(frames) == 3
        assert [f.pose_hint for f in frames] == poses

class TestEnrollmentFaceDetector:
    def test_detection_and_landmarks(self, detector):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 240
        face_sample = create_synthetic_face(w=160, h=160)
        frame[100:260, 200:360] = face_sample

        faces = detector.detect_all_faces(frame)
        assert len(faces) >= 1
        primary = detector.detect_primary_face(frame)
        assert primary is not None
        assert primary.bbox[2] > primary.bbox[0]
        assert primary.face_crop.size > 0
        assert primary.left_eye is not None
        assert primary.right_eye is not None

class TestFaceAligner:
    def test_canonical_arcface_alignment(self, aligner):
        face = create_synthetic_face(w=140, h=140)
        left_eye = (45, 55)
        right_eye = (95, 55)

        aligned = aligner.align_face(face, left_eye=left_eye, right_eye=right_eye)
        assert aligned.shape == (112, 112, 3)

    def test_tilted_face_roll_correction(self, aligner):
        # Face with 20 degree tilt
        face = create_synthetic_face(w=150, h=150)
        # Left eye lower than right eye
        left_eye = (40, 70)
        right_eye = (100, 48)

        aligned = aligner.align_face(face, left_eye=left_eye, right_eye=right_eye)
        assert aligned.shape == (112, 112, 3)

class TestEnrollmentQualityEvaluator:
    def test_high_quality_face_passes(self, quality_evaluator):
        face = create_synthetic_face(w=120, h=120, blurred=False)
        report = quality_evaluator.evaluate(
            face,
            detection_confidence=0.98,
            left_eye=(38, 48),
            right_eye=(82, 48),
            nose_tip=(60, 65),
            mouth_center=(60, 95)
        )
        assert report.face_width == 120.0
        assert report.blur_score > 100.0
        assert report.quality_score >= 0.65
        assert report.is_acceptable is True
        assert len(report.failure_reasons) == 0

    def test_low_resolution_rejection(self, quality_evaluator):
        # Face width 60px (below 80px target)
        face_small = create_synthetic_face(w=60, h=60)
        report = quality_evaluator.evaluate(face_small)
        assert report.face_width < 80.0
        assert report.is_acceptable is False
        assert any("below 80px target" in r for r in report.failure_reasons)

    def test_blur_rejection(self, quality_evaluator):
        face_blurred = create_synthetic_face(w=120, h=120, blurred=True)
        report = quality_evaluator.evaluate(face_blurred)
        assert report.blur_score < 100.0
        assert report.is_acceptable is False
        assert any("blurred" in r for r in report.failure_reasons)

    def test_extreme_yaw_pose_rejection(self, quality_evaluator):
        face = create_synthetic_face(w=120, h=120)
        # Nose heavily shifted to the side relative to eyes -> high yaw angle
        report = quality_evaluator.evaluate(
            face,
            left_eye=(30, 45),
            right_eye=(70, 45),
            nose_tip=(95, 60),  # Extreme offset
            mouth_center=(60, 95)
        )
        assert abs(report.yaw) > 30.0
        assert report.is_acceptable is False
        assert any("yaw" in r for r in report.failure_reasons)
