"""Camera Quality Analyzer evaluating CCTV camera suitability, resolution, sharpness,
lighting, and face resolution in pixels to objectively optimize camera placement.
"""
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np

@dataclass
class CameraQualityReport:
    camera_id: str
    resolution: str
    width: int
    height: int
    fps: float
    blur_score: float                # Laplacian variance (>100 is crisp)
    lighting_score: float            # 0.0 to 1.0 (normalized luminance & contrast)
    average_face_width_px: float
    average_face_height_px: float
    capture_quality: str             # "GOOD", "MARGINAL", "POOR"
    face_count: int

    def to_dict(self) -> dict:
        return asdict(self)

class CameraQualityAnalyzer:
    def __init__(self, camera_id: str = "CAM01"):
        self.camera_id = camera_id

    def assess_frame(
        self,
        frame: np.ndarray,
        fps: float = 25.0,
        face_bboxes: Optional[List[Tuple[int, int, int, int]]] = None
    ) -> CameraQualityReport:
        if frame is None or frame.size == 0:
            return CameraQualityReport(
                camera_id=self.camera_id,
                resolution="0x0",
                width=0,
                height=0,
                fps=fps,
                blur_score=0.0,
                lighting_score=0.0,
                average_face_width_px=0.0,
                average_face_height_px=0.0,
                capture_quality="POOR",
                face_count=0
            )

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        # 1. Blur / Sharpness via Laplacian Variance
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        blur_score = round(float(lap.var()), 2)

        # 2. Lighting Score (Penalize severe underexposure and overexposure)
        mean_lum = float(np.mean(gray))
        std_lum = float(np.std(gray))
        # Ideal luminance ~120, standard deviation ~50
        lum_diff = abs(mean_lum - 120.0)
        lighting_score = max(0.0, min(1.0, 1.0 - (lum_diff / 120.0) + (std_lum / 200.0)))
        lighting_score = round(lighting_score, 2)

        # 3. Face Pixel Dimensions
        avg_fw = 0.0
        avg_fh = 0.0
        face_count = 0
        if face_bboxes and len(face_bboxes) > 0:
            widths = [(b[2] - b[0]) for b in face_bboxes]
            heights = [(b[3] - b[1]) for b in face_bboxes]
            avg_fw = round(float(np.mean(widths)), 1)
            avg_fh = round(float(np.mean(heights)), 1)
            face_count = len(face_bboxes)

        # 4. Overall Rating Classification
        # Face size: <20px unreliable, 20-40px marginal, >=40px good
        # Blur: <60 poor, 60-100 marginal, >=100 good
        if (face_count > 0 and avg_fw < 20.0) or blur_score < 40.0 or lighting_score < 0.35:
            quality = "POOR"
        elif (face_count > 0 and avg_fw < 40.0) or blur_score < 80.0 or lighting_score < 0.60:
            quality = "MARGINAL"
        else:
            quality = "GOOD"

        return CameraQualityReport(
            camera_id=self.camera_id,
            resolution=f"{w}x{h}",
            width=w,
            height=h,
            fps=round(fps, 1),
            blur_score=blur_score,
            lighting_score=lighting_score,
            average_face_width_px=avg_fw,
            average_face_height_px=avg_fh,
            capture_quality=quality,
            face_count=face_count
        )
