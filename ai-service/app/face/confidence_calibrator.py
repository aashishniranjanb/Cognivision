"""Biometric Confidence Calibrator: Maps raw cosine distances and capture conditions to calibrated posterior match probabilities."""
import numpy as np
from typing import Dict, Any, Optional

class BiometricConfidenceCalibrator:
    def __init__(
        self,
        sigmoid_midpoint: float = 0.62,
        sigmoid_slope: float = 14.0,
        benchmark_face_width: float = 80.0,
        benchmark_blur_score: float = 100.0
    ):
        self.s0 = sigmoid_midpoint
        self.k = sigmoid_slope
        self.benchmark_width = benchmark_face_width
        self.benchmark_blur = benchmark_blur_score

    def calibrate(
        self,
        raw_cosine_similarity: float,
        face_width: float = 85.0,
        blur_score: float = 110.0,
        illumination_score: float = 0.85,
        consecutive_hits: int = 1
    ) -> float:
        """Calculates calibrated probability score P(Match | Evidence) bounded in [0.01, 0.999]."""
        # 1. Base Sigmoid Probability
        # For similarity=0.62 -> P0 = 0.50; similarity=0.75 -> P0 = 0.86; similarity=0.85 -> P0 = 0.96
        p0 = 1.0 / (1.0 + np.exp(-self.k * (raw_cosine_similarity - self.s0)))

        # 2. Optical Scaling Factors (Plan 24 Step 3)
        # Face width factor: scales down if width < 80px
        width_ratio = max(0.1, face_width / self.benchmark_width)
        c_width = min(1.05, width_ratio ** 0.6)

        # Sharpness factor: penalizes blur below 100 threshold
        blur_ratio = max(0.1, blur_score / self.benchmark_blur)
        c_blur = min(1.05, blur_ratio ** 0.4)

        # Illumination factor: penalizes bad exposure
        c_illum = 0.85 + 0.15 * np.clip(illumination_score, 0.0, 1.0)

        # 3. Temporal Consistency Bonus
        # Successive consecutive frame matches boost confidence
        temporal_bonus = 1.0 + 0.03 * min(4, max(0, consecutive_hits - 1))

        # Modulate
        calibrated = p0 * c_width * c_blur * c_illum * temporal_bonus
        return float(np.clip(round(calibrated, 4), 0.01, 0.999))
