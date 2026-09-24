"""Unknown Person Rejection & Audit Engine: Differentiates between degraded enrolled faces and genuine unknown visitors."""
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import time

@dataclass
class UnknownClassificationResult:
    is_unknown_visitor: bool
    classification: str  # "GENUINE_UNKNOWN", "POOR_QUALITY_FACE", "IDENTITY_UNCERTAIN", "KNOWN_STUDENT"
    confidence: float
    max_database_similarity: float
    face_quality_score: float
    details: str
    action_required: str  # "DISPATCH_ALARM", "RE_ACQUIRE_FACE", "FLAG_FOR_REVIEW", "NONE"

class UnknownPersonClassifier:
    def __init__(
        self,
        unknown_threshold: float = 0.52,
        uncertain_threshold: float = 0.65,
        min_quality_for_confirmed_unknown: float = 0.70
    ):
        self.unknown_threshold = unknown_threshold
        self.uncertain_threshold = uncertain_threshold
        self.min_quality_for_confirmed_unknown = min_quality_for_confirmed_unknown

    def classify_observation(
        self,
        max_similarity: float,
        face_quality_score: float,
        face_width: float,
        blur_score: float,
        temporal_track_frames: int = 1
    ) -> UnknownClassificationResult:
        """Classifies a face observation as a genuine unknown visitor, poor quality capture, or uncertain identity."""
        # Case 1: High similarity -> clearly known enrolled student
        if max_similarity >= self.uncertain_threshold:
            return UnknownClassificationResult(
                is_unknown_visitor=False,
                classification="KNOWN_STUDENT",
                confidence=round(max_similarity, 3),
                max_database_similarity=round(max_similarity, 3),
                face_quality_score=round(face_quality_score, 3),
                details="Observation verified against registered student template.",
                action_required="NONE"
            )

        # Case 2: Low similarity, but face quality is degraded (small, blurry, dark)
        # We should NOT brand a student as an unknown intruder just because of motion blur or distance!
        if face_quality_score < self.min_quality_for_confirmed_unknown or face_width < 75.0 or blur_score < 90.0:
            return UnknownClassificationResult(
                is_unknown_visitor=False,
                classification="POOR_QUALITY_FACE",
                confidence=round(1.0 - face_quality_score, 3),
                max_database_similarity=round(max_similarity, 3),
                face_quality_score=round(face_quality_score, 3),
                details=f"Face degraded (width: {face_width:.0f}px, blur: {blur_score:.1f}). Awaiting clearer corridor frame.",
                action_required="RE_ACQUIRE_FACE"
            )

        # Case 3: High optical quality (clear, crisp face) with low similarity
        # This is a genuine unregistered visitor / intruder
        if max_similarity < self.unknown_threshold:
            # If confirmed over multiple consecutive frames, high confidence unknown
            conf = min(0.98, 0.75 + 0.05 * temporal_track_frames)
            return UnknownClassificationResult(
                is_unknown_visitor=True,
                classification="GENUINE_UNKNOWN",
                confidence=round(conf, 3),
                max_database_similarity=round(max_similarity, 3),
                face_quality_score=round(face_quality_score, 3),
                details=f"Crisp face (quality {face_quality_score:.2f}) does not match any enrolled student (max sim {max_similarity:.3f}).",
                action_required="DISPATCH_ALARM"
            )

        # Case 4: Ambiguous middle zone (0.52 to 0.65)
        return UnknownClassificationResult(
            is_unknown_visitor=False,
            classification="IDENTITY_UNCERTAIN",
            confidence=round(max_similarity, 3),
            max_database_similarity=round(max_similarity, 3),
            face_quality_score=round(face_quality_score, 3),
            details=f"Borderline similarity {max_similarity:.3f} requires multimodal fusion or operator audit.",
            action_required="FLAG_FOR_REVIEW"
        )
