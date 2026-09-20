"""Face Quality Assessment module calculating objective reliability features."""
import cv2
import numpy as np
from dataclasses import dataclass

@dataclass
class FaceQualityReport:
    overall_reliability: float   # Normalized 0.0 to 1.0
    resolution_score: float      # Adequate pixel size
    sharpness_score: float       # Laplacian variance blur metric
    brightness_score: float      # Illumination uniformity
    is_usable: bool

class FaceQualityAssessor:
    def __init__(self, min_face_size: int = 50, blur_thresh: float = 65.0):
        self.min_face_size = min_face_size
        self.blur_thresh = blur_thresh

    def assess(self, face_crop: np.ndarray) -> FaceQualityReport:
        if face_crop is None or face_crop.size == 0:
            return FaceQualityReport(0.0, 0.0, 0.0, 0.0, False)

        h, w = face_crop.shape[:2]

        # 1. Resolution Score (Target: 80x80px or higher for clear face)
        min_dim = min(h, w)
        res_score = min(1.0, min_dim / 112.0)

        # 2. Sharpness / Blur metric using Laplacian variance
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY) if len(face_crop.shape) == 3 else face_crop
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(1.0, laplacian_var / 250.0)

        # 3. Brightness / Illumination Score (optimal mean between 60 and 190)
        mean_brightness = float(np.mean(gray))
        if 65.0 <= mean_brightness <= 185.0:
            bright_score = 1.0
        elif mean_brightness < 65.0:
            bright_score = max(0.0, mean_brightness / 65.0)
        else:
            bright_score = max(0.0, (255.0 - mean_brightness) / 70.0)

        # Weighted aggregate reliability score
        overall = 0.35 * res_score + 0.40 * sharpness_score + 0.25 * bright_score
        is_usable = (min_dim >= self.min_face_size) and (laplacian_var >= self.blur_thresh) and (overall >= 0.45)

        return FaceQualityReport(
            overall_reliability=float(np.clip(overall, 0.0, 1.0)),
            resolution_score=float(res_score),
            sharpness_score=float(sharpness_score),
            brightness_score=float(bright_score),
            is_usable=is_usable
        )
