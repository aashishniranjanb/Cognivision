"""Enrollment Quality Gate: Admission controller enforcing strict Plan 24 optical criteria before embedding extraction."""
import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass

from app.face.enrollment_detector import EnrollmentFaceDetector, EnrollmentFace
from app.face.aligner import FaceAligner
from app.face.quality_evaluator import EnrollmentQualityEvaluator, EnrollmentQualityReport

@dataclass
class QualityGateResult:
    passed: bool
    quality_report: EnrollmentQualityReport
    aligned_face: Optional[np.ndarray] = None
    face_bbox: Optional[Tuple[int, int, int, int]] = None
    failure_reasons: List[str] = None

    def __post_init__(self):
        if self.failure_reasons is None:
            self.failure_reasons = []

class EnrollmentQualityGate:
    def __init__(
        self,
        min_face_width: float = 80.0,
        min_blur_score: float = 100.0,
        min_quality_score: float = 0.65,
        detector: Optional[EnrollmentFaceDetector] = None,
        aligner: Optional[FaceAligner] = None,
        evaluator: Optional[EnrollmentQualityEvaluator] = None
    ):
        self.detector = detector or EnrollmentFaceDetector(min_face_size=(int(min_face_width * 0.7), int(min_face_width * 0.7)))
        self.aligner = aligner or FaceAligner(output_size=(112, 112))
        self.evaluator = evaluator or EnrollmentQualityEvaluator(
            min_face_width=min_face_width,
            min_blur_score=min_blur_score,
            min_quality_score=min_quality_score
        )

    def process_frame(self, frame: np.ndarray) -> QualityGateResult:
        """Runs complete detection, quality gate evaluation, and landmark alignment."""
        if frame is None or frame.size == 0:
            empty_report = EnrollmentQualityReport(
                face_width=0, blur_score=0, illumination_score=0,
                yaw=0, pitch=0, roll=0, occlusion=1.0,
                detection_confidence=0, quality_score=0,
                is_acceptable=False, failure_reasons=["Empty input frame"]
            )
            return QualityGateResult(passed=False, quality_report=empty_report, failure_reasons=["Empty input frame"])

        # 1. Detect primary face
        primary_face = self.detector.detect_primary_face(frame)
        if not primary_face:
            empty_report = EnrollmentQualityReport(
                face_width=0, blur_score=0, illumination_score=0,
                yaw=0, pitch=0, roll=0, occlusion=1.0,
                detection_confidence=0, quality_score=0,
                is_acceptable=False, failure_reasons=["No face detected in frame"]
            )
            return QualityGateResult(passed=False, quality_report=empty_report, failure_reasons=["No face detected in frame"])

        # 2. Evaluate face quality against Plan 24 criteria
        report = self.evaluator.evaluate(
            face_crop=primary_face.face_crop,
            detection_confidence=primary_face.confidence,
            left_eye=primary_face.left_eye,
            right_eye=primary_face.right_eye,
            nose_tip=primary_face.nose_tip,
            mouth_center=primary_face.mouth_center
        )

        if not report.is_acceptable:
            return QualityGateResult(
                passed=False,
                quality_report=report,
                face_bbox=primary_face.bbox,
                failure_reasons=report.failure_reasons
            )

        # 3. Align face to canonical 112x112 ArcFace coordinate space
        aligned = self.aligner.align_face(
            face_crop=primary_face.face_crop,
            left_eye=primary_face.left_eye,
            right_eye=primary_face.right_eye,
            nose_tip=primary_face.nose_tip,
            mouth_center=primary_face.mouth_center
        )

        return QualityGateResult(
            passed=True,
            quality_report=report,
            aligned_face=aligned,
            face_bbox=primary_face.bbox,
            failure_reasons=[]
        )
