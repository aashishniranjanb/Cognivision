"""Multi-Image Biometric Enrollment Engine: Orchestrates Quality Gate, Embedding Extraction, Outlier Rejection, and Template Aggregation."""
import cv2
import os
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from app.face.quality_gate import EnrollmentQualityGate, QualityGateResult
from app.face.arcface_embedder import ArcFaceEmbeddingService
from app.face.outlier_rejection import EmbeddingOutlierFilter, OutlierFilterResult
from app.face.template_aggregator import TemplateAggregator, AggregatedTemplateResult
from app.biometrics.repository import BiometricRepository
from app.biometrics.schemas import StudentCreate, EmbeddingVariantCreate

@dataclass
class ImageEnrollmentSample:
    index: int
    source_name: str
    passed_gate: bool
    quality_score: float
    is_outlier: bool = False
    embedding: Optional[np.ndarray] = None
    aligned_crop: Optional[np.ndarray] = None
    failure_reasons: List[str] = field(default_factory=list)

@dataclass
class MultiImageEnrollmentResult:
    student_id: str
    success: bool
    status: str  # "READY", "RE_ENROLL_REQUIRED", "FAILED"
    total_images_submitted: int
    passed_quality_gate: int
    rejected_quality_gate: int
    outliers_rejected: int
    final_variants_count: int
    enrollment_quality: float
    intra_class_compactness: float
    canonical_embedding: Optional[List[float]] = None
    samples_detail: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""

class MultiImageEnrollmentEngine:
    def __init__(
        self,
        min_required_variants: int = 3,
        biometric_repo: Optional[BiometricRepository] = None,
        quality_gate: Optional[EnrollmentQualityGate] = None,
        embedder: Optional[ArcFaceEmbeddingService] = None,
        outlier_filter: Optional[EmbeddingOutlierFilter] = None,
        aggregator: Optional[TemplateAggregator] = None
    ):
        self.min_required_variants = min_required_variants
        self.repo = biometric_repo or BiometricRepository()
        self.quality_gate = quality_gate or EnrollmentQualityGate()
        self.embedder = embedder or ArcFaceEmbeddingService()
        self.outlier_filter = outlier_filter or EmbeddingOutlierFilter()
        self.aggregator = aggregator or TemplateAggregator(embedding_dim=512)

    def enroll_student(
        self,
        student_id: str,
        images: List[Any],  # List of np.ndarray frames or str file paths
        student_metadata: Optional[Dict[str, Any]] = None,
        save_to_database: bool = True
    ) -> MultiImageEnrollmentResult:
        """Processes 5 to 10 enrollment captures through the full V1.3 pipeline."""
        total = len(images)
        if total == 0:
            return MultiImageEnrollmentResult(
                student_id=student_id, success=False, status="FAILED",
                total_images_submitted=0, passed_quality_gate=0,
                rejected_quality_gate=0, outliers_rejected=0,
                final_variants_count=0, enrollment_quality=0.0,
                intra_class_compactness=0.0, message="No images provided for enrollment."
            )

        # Ensure student exists in repository if metadata provided
        if save_to_database:
            existing = self.repo.get_student(student_id)
            if not existing and student_metadata:
                self.repo.create_student(StudentCreate(
                    student_id=student_id,
                    name=student_metadata.get("name", f"Student {student_id}"),
                    department=student_metadata.get("department", "ECE"),
                    year=student_metadata.get("year", 4),
                    register_number=student_metadata.get("register_number", f"RA23{student_id}")
                ))

        processed_samples: List[ImageEnrollmentSample] = []
        valid_crops: List[np.ndarray] = []
        valid_indices: List[int] = []

        # Step 1: Quality Gate & Alignment for each submitted image
        for idx, img_item in enumerate(images):
            frame = self._load_frame(img_item)
            src_name = str(img_item) if isinstance(img_item, (str, Path)) else f"frame_{idx+1}"

            gate_res: QualityGateResult = self.quality_gate.process_frame(frame)
            if not gate_res.passed:
                processed_samples.append(ImageEnrollmentSample(
                    index=idx,
                    source_name=src_name,
                    passed_gate=False,
                    quality_score=gate_res.quality_report.quality_score,
                    failure_reasons=gate_res.failure_reasons
                ))
            else:
                processed_samples.append(ImageEnrollmentSample(
                    index=idx,
                    source_name=src_name,
                    passed_gate=True,
                    quality_score=gate_res.quality_report.quality_score,
                    aligned_crop=gate_res.aligned_face
                ))
                valid_crops.append(gate_res.aligned_face)
                valid_indices.append(idx)

        passed_gate_count = len(valid_crops)

        # Check if enough images passed quality gate
        if passed_gate_count < self.min_required_variants:
            if save_to_database:
                self.repo.upsert_biometric_profile(
                    student_id=student_id,
                    status="RE_ENROLL_REQUIRED",
                    enrolled_images=passed_gate_count
                )
            return MultiImageEnrollmentResult(
                student_id=student_id,
                success=False,
                status="RE_ENROLL_REQUIRED",
                total_images_submitted=total,
                passed_quality_gate=passed_gate_count,
                rejected_quality_gate=total - passed_gate_count,
                outliers_rejected=0,
                final_variants_count=passed_gate_count,
                enrollment_quality=0.0,
                intra_class_compactness=0.0,
                samples_detail=[self._sample_to_dict(s) for s in processed_samples],
                message=f"Only {passed_gate_count} of {total} images passed the Plan 24 quality gate (minimum {self.min_required_variants} required)."
            )

        # Step 2: ArcFace 512-D Embedding Extraction
        embeddings = self.embedder.extract_batch(valid_crops)
        quality_scores = [processed_samples[idx].quality_score for idx in valid_indices]

        # Step 3: Outlier Rejection
        outlier_res: OutlierFilterResult = self.outlier_filter.filter_outliers(
            embeddings=embeddings, quality_scores=quality_scores
        )

        for rej_idx in outlier_res.rejected_indices:
            orig_idx = valid_indices[rej_idx]
            processed_samples[orig_idx].is_outlier = True
            processed_samples[orig_idx].failure_reasons.append(
                outlier_res.rejection_reasons.get(rej_idx, "Pairwise identity divergence (outlier)")
            )

        accepted_embeddings = [embeddings[i] for i in outlier_res.accepted_indices]
        accepted_qualities = [quality_scores[i] for i in outlier_res.accepted_indices]
        accepted_orig_indices = [valid_indices[i] for i in outlier_res.accepted_indices]

        # Step 4: Quality-Weighted Centroid Aggregation
        agg_res: AggregatedTemplateResult = self.aggregator.aggregate(
            embeddings=accepted_embeddings,
            quality_scores=accepted_qualities
        )

        # Step 5: Persistence into Biometric Database
        if save_to_database:
            # 1. Save accepted variants
            for pos, orig_idx in enumerate(accepted_orig_indices):
                sample = processed_samples[orig_idx]
                emb_list = accepted_embeddings[pos].tolist()
                self.repo.add_variant(student_id, EmbeddingVariantCreate(
                    embedding=emb_list,
                    quality_score=sample.quality_score,
                    source_image=sample.source_name
                ))

            # 2. Save canonical template profile
            self.repo.upsert_biometric_profile(
                student_id=student_id,
                template_embedding=agg_res.canonical_embedding.tolist(),
                template_version=1,
                enrollment_quality=agg_res.enrollment_quality,
                enrolled_images=len(accepted_embeddings),
                status="READY"
            )

        return MultiImageEnrollmentResult(
            student_id=student_id,
            success=True,
            status="READY",
            total_images_submitted=total,
            passed_quality_gate=passed_gate_count,
            rejected_quality_gate=total - passed_gate_count,
            outliers_rejected=len(outlier_res.rejected_indices),
            final_variants_count=len(accepted_embeddings),
            enrollment_quality=agg_res.enrollment_quality,
            intra_class_compactness=agg_res.intra_class_compactness,
            canonical_embedding=agg_res.canonical_embedding.tolist(),
            samples_detail=[self._sample_to_dict(s) for s in processed_samples],
            message=f"Enrollment successful: {len(accepted_embeddings)} variants aggregated into ArcFace template (Quality: {agg_res.enrollment_quality*100:.1f}%, Compactness: {agg_res.intra_class_compactness:.3f})."
        )

    def _load_frame(self, item: Any) -> np.ndarray:
        if isinstance(item, np.ndarray):
            return item
        if isinstance(item, (str, Path)):
            p = str(item)
            if os.path.exists(p):
                return cv2.imread(p)
        return np.array([])

    def _sample_to_dict(self, sample: ImageEnrollmentSample) -> Dict[str, Any]:
        return {
            "index": sample.index + 1,
            "source": sample.source_name,
            "passed_gate": sample.passed_gate,
            "quality_score": round(sample.quality_score, 3),
            "is_outlier": sample.is_outlier,
            "failure_reasons": sample.failure_reasons
        }
