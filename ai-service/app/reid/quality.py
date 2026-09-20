"""Body Re-ID Quality Assessor evaluating resolution, aspect ratio, visibility, and blur."""
import cv2
import numpy as np
from dataclasses import dataclass

@dataclass
class BodyQualityReport:
    overall_reliability: float   # Normalized 0.0 to 1.0
    resolution_score: float      # Adequate width & height
    aspect_ratio_score: float    # Human standing aspect ratio (approx 1:2 to 1:3.5)
    sharpness_score: float       # Laplacian sharpness variance
    is_usable: bool

class BodyQualityAssessor:
    def __init__(self, min_height: int = 100, min_width: int = 40):
        self.min_height = min_height
        self.min_width = min_width

    def assess(self, person_crop: np.ndarray) -> BodyQualityReport:
        if person_crop is None or person_crop.size == 0:
            return BodyQualityReport(0.0, 0.0, 0.0, 0.0, False)

        h, w = person_crop.shape[:2]

        # 1. Resolution Score (Target: 256x128px standard Re-ID crop)
        res_score = min(1.0, (h * w) / (256.0 * 128.0))

        # 2. Aspect Ratio (Typical full body: height is 1.8x to 3.5x width)
        ratio = h / float(w) if w > 0 else 0
        if 1.6 <= ratio <= 3.8:
            ar_score = 1.0
        elif 1.0 <= ratio < 1.6:
            ar_score = max(0.2, ratio / 1.6)
        else:
            ar_score = max(0.1, 3.8 / max(ratio, 0.1))

        # 3. Sharpness Variance
        gray = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY) if len(person_crop.shape) == 3 else person_crop
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(1.0, lap_var / 150.0)

        overall = 0.40 * res_score + 0.35 * ar_score + 0.25 * sharpness_score
        is_usable = (h >= self.min_height) and (w >= self.min_width) and (overall >= 0.35)

        return BodyQualityReport(
            overall_reliability=float(np.clip(overall, 0.0, 1.0)),
            resolution_score=float(res_score),
            aspect_ratio_score=float(ar_score),
            sharpness_score=float(sharpness_score),
            is_usable=is_usable
        )
