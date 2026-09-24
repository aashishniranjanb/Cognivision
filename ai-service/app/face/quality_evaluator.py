"""Comprehensive Face Quality Evaluator for Biometric Enrollment Gates (Plan 24 Criteria)."""
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class EnrollmentQualityReport:
    face_width: float
    blur_score: float
    illumination_score: float
    yaw: float
    pitch: float
    roll: float
    occlusion: float
    detection_confidence: float
    quality_score: float
    is_acceptable: bool
    failure_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "face_width": round(self.face_width, 1),
            "blur_score": round(self.blur_score, 1),
            "illumination_score": round(self.illumination_score, 3),
            "yaw": round(self.yaw, 1),
            "pitch": round(self.pitch, 1),
            "roll": round(self.roll, 1),
            "occlusion": round(self.occlusion, 3),
            "detection_confidence": round(self.detection_confidence, 3),
            "quality_score": round(self.quality_score, 3),
            "is_acceptable": self.is_acceptable,
            "failure_reasons": self.failure_reasons
        }

class EnrollmentQualityEvaluator:
    def __init__(
        self,
        min_face_width: float = 80.0,
        min_blur_score: float = 100.0,
        min_illumination: float = 0.40,
        max_yaw: float = 30.0,
        max_pitch: float = 25.0,
        max_roll: float = 20.0,
        max_occlusion: float = 0.25,
        min_quality_score: float = 0.65
    ):
        self.min_face_width = min_face_width
        self.min_blur_score = min_blur_score
        self.min_illumination = min_illumination
        self.max_yaw = max_yaw
        self.max_pitch = max_pitch
        self.max_roll = max_roll
        self.max_occlusion = max_occlusion
        self.min_quality_score = min_quality_score

    def evaluate(
        self,
        face_crop: np.ndarray,
        detection_confidence: float = 0.95,
        left_eye: Optional[Tuple[int, int]] = None,
        right_eye: Optional[Tuple[int, int]] = None,
        nose_tip: Optional[Tuple[int, int]] = None,
        mouth_center: Optional[Tuple[int, int]] = None
    ) -> EnrollmentQualityReport:
        if face_crop is None or face_crop.size == 0:
            return EnrollmentQualityReport(
                face_width=0.0, blur_score=0.0, illumination_score=0.0,
                yaw=0.0, pitch=0.0, roll=0.0, occlusion=1.0,
                detection_confidence=0.0, quality_score=0.0,
                is_acceptable=False, failure_reasons=["Empty or invalid face frame"]
            )

        h, w = face_crop.shape[:2]
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY) if len(face_crop.shape) == 3 else face_crop
        reasons: List[str] = []

        # 1. Face Width (Plan 24 Step 3 target: >= 80px)
        face_width = float(w)
        if face_width < self.min_face_width:
            reasons.append(f"Face width {face_width:.0f}px below {self.min_face_width:.0f}px target")
        width_ratio = min(1.0, face_width / 112.0)

        # 2. Sharpness (Laplacian blur variance >= 100)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if blur_score < self.min_blur_score:
            reasons.append(f"Sharpness {blur_score:.1f} below {self.min_blur_score:.1f} threshold (blurred image)")
        blur_ratio = min(1.0, blur_score / 200.0)

        # 3. Illumination Score (Mean intensity & contrast balance)
        mean_intensity = float(np.mean(gray))
        std_intensity = float(np.std(gray))
        if 60.0 <= mean_intensity <= 200.0 and std_intensity > 25.0:
            illumination_score = 1.0 - abs(mean_intensity - 128.0) / 128.0 * 0.4
        elif mean_intensity < 60.0:
            illumination_score = max(0.0, mean_intensity / 60.0 * 0.7)
            reasons.append("Under-exposed / low light")
        else:
            illumination_score = max(0.0, (255.0 - mean_intensity) / 55.0 * 0.7)
            reasons.append("Over-exposed / washed out lighting")

        # 4. Pose Estimation (Yaw, Pitch, Roll)
        roll, yaw, pitch = self._estimate_pose_angles(w, h, left_eye, right_eye, nose_tip, mouth_center)

        if abs(yaw) > self.max_yaw:
            reasons.append(f"Extreme yaw angle {yaw:+.1f}° exceeds ±{self.max_yaw:.0f}°")
        if abs(pitch) > self.max_pitch:
            reasons.append(f"Extreme pitch angle {pitch:+.1f}° exceeds ±{self.max_pitch:.0f}°")
        if abs(roll) > self.max_roll:
            reasons.append(f"Extreme head tilt {roll:+.1f}° exceeds ±{self.max_roll:.0f}°")

        pose_penalty = min(1.0, (abs(yaw) / 45.0 + abs(pitch) / 35.0 + abs(roll) / 30.0) / 3.0)
        pose_score = max(0.0, 1.0 - pose_penalty)

        # 5. Occlusion Estimation
        occlusion = self._estimate_occlusion(gray)
        if occlusion > self.max_occlusion:
            reasons.append(f"Occlusion risk {occlusion*100:.1f}% exceeds {self.max_occlusion*100:.0f}% tolerance")

        # Composite Quality Score calculation
        # Weights: Resolution (25%), Sharpness (30%), Illumination (20%), Pose (15%), Confidence (10%)
        composite = (
            0.25 * width_ratio +
            0.30 * blur_ratio +
            0.20 * illumination_score +
            0.15 * pose_score +
            0.10 * detection_confidence
        ) * (1.0 - occlusion * 0.5)

        quality_score = float(np.clip(composite, 0.0, 1.0))
        is_acceptable = (len(reasons) == 0) and (quality_score >= self.min_quality_score)

        return EnrollmentQualityReport(
            face_width=face_width,
            blur_score=blur_score,
            illumination_score=illumination_score,
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            occlusion=occlusion,
            detection_confidence=detection_confidence,
            quality_score=quality_score,
            is_acceptable=is_acceptable,
            failure_reasons=reasons
        )

    def _estimate_pose_angles(
        self,
        w: int,
        h: int,
        left_eye: Optional[Tuple[int, int]],
        right_eye: Optional[Tuple[int, int]],
        nose_tip: Optional[Tuple[int, int]],
        mouth_center: Optional[Tuple[int, int]]
    ) -> Tuple[float, float, float]:
        """Estimates approximate head pose: Roll, Yaw, Pitch in degrees from facial geometry."""
        # 1. Roll: Angle between eyes
        roll = 0.0
        if left_eye and right_eye:
            dx = right_eye[0] - left_eye[0]
            dy = right_eye[1] - left_eye[1]
            roll = float(np.degrees(np.arctan2(dy, dx)))

        # 2. Yaw: Asymmetry of nose relative to eye centers
        yaw = 0.0
        if left_eye and right_eye and nose_tip:
            eye_mid_x = (left_eye[0] + right_eye[0]) / 2.0
            eye_dist = max(1.0, abs(right_eye[0] - left_eye[0]))
            nose_offset = nose_tip[0] - eye_mid_x
            # Normalized offset roughly maps to yaw degrees
            yaw = float(np.clip((nose_offset / eye_dist) * 60.0, -60.0, 60.0))

        # 3. Pitch: Vertical ratio between eye line, nose, and mouth
        pitch = 0.0
        if left_eye and right_eye and nose_tip and mouth_center:
            eye_y = (left_eye[1] + right_eye[1]) / 2.0
            nose_y = nose_tip[1]
            mouth_y = mouth_center[1]
            upper = max(1.0, nose_y - eye_y)
            lower = max(1.0, mouth_y - nose_y)
            ratio = upper / lower
            pitch = float(np.clip((ratio - 1.0) * 35.0, -45.0, 45.0))

        return roll, yaw, pitch

    def _estimate_occlusion(self, face_gray: np.ndarray) -> float:
        """Estimates occlusion by measuring gradient uniformity across lower half of face."""
        h, w = face_gray.shape[:2]
        lower_face = face_gray[int(h * 0.5):, :]
        grad_x = cv2.Sobel(lower_face, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(lower_face, cv2.CV_64F, 0, 1, ksize=3)
        edge_energy = float(np.mean(np.sqrt(grad_x ** 2 + grad_y ** 2)))

        # Occlusion (e.g. mask or hand) produces low facial texture in lower face
        if edge_energy < 15.0:
            return 0.35  # Possible smooth mask or uniform occlusion
        return 0.04
