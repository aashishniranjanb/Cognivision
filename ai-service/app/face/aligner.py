"""Facial Landmark Aligner: Performs similarity transformation into canonical 112x112 ArcFace standard coordinate space."""
import cv2
import numpy as np
from typing import Tuple, Optional

# Standard ArcFace 5-point canonical reference coordinates in 112x112 pixel space
ARCFACE_REFERENCE_LANDMARKS = np.array([
    [38.2946, 51.6963],  # Left eye
    [73.5318, 51.5014],  # Right eye
    [56.0252, 71.7366],  # Nose tip
    [41.5493, 92.3655],  # Mouth left corner
    [70.7299, 92.2041]   # Mouth right corner
], dtype=np.float32)

class FaceAligner:
    def __init__(self, output_size: Tuple[int, int] = (112, 112)):
        self.output_size = output_size
        self.ref_landmarks = ARCFACE_REFERENCE_LANDMARKS

    def align_face(
        self,
        face_crop: np.ndarray,
        left_eye: Optional[Tuple[int, int]] = None,
        right_eye: Optional[Tuple[int, int]] = None,
        nose_tip: Optional[Tuple[int, int]] = None,
        mouth_center: Optional[Tuple[int, int]] = None
    ) -> np.ndarray:
        """Aligns a face crop to canonical ArcFace 112x112 using similarity/affine transformation."""
        if face_crop is None or face_crop.size == 0:
            return np.zeros((self.output_size[1], self.output_size[0], 3), dtype=np.uint8)

        h, w = face_crop.shape[:2]

        # If eyes are provided, calculate roll angle and scale
        if left_eye is not None and right_eye is not None:
            lx, ly = left_eye
            rx, ry = right_eye
            dx = rx - lx
            dy = ry - ly
            dist = np.sqrt(dx ** 2 + dy ** 2)

            if dist > 5:
                # Compute angle between eyes
                angle = np.degrees(np.arctan2(dy, dx))
                # Compute eye midpoint
                eyes_center = ((lx + rx) / 2.0, (ly + ry) / 2.0)

                # Reference eye distance in 112x112 ArcFace space
                ref_dist = self.ref_landmarks[1][0] - self.ref_landmarks[0][0]  # ~35.24 px
                scale = ref_dist / dist

                # Get rotation matrix around eyes center
                M = cv2.getRotationMatrix2D(eyes_center, angle, scale)

                # Shift center so eyes align with reference eye center
                ref_eye_center = (
                    (self.ref_landmarks[0][0] + self.ref_landmarks[1][0]) / 2.0,
                    (self.ref_landmarks[0][1] + self.ref_landmarks[1][1]) / 2.0
                )
                tX = ref_eye_center[0] - eyes_center[0]
                tY = ref_eye_center[1] - eyes_center[1]
                M[0, 2] += tX
                M[1, 2] += tY

                aligned = cv2.warpAffine(
                    face_crop,
                    M,
                    self.output_size,
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REFLECT_101
                )
                return aligned

        # Fallback: Aspect-preserving center crop and resize to 112x112
        return self._center_crop_and_resize(face_crop)

    def _center_crop_and_resize(self, face_crop: np.ndarray) -> np.ndarray:
        h, w = face_crop.shape[:2]
        min_dim = min(h, w)
        start_x = (w - min_dim) // 2
        start_y = (h - min_dim) // 2
        square_crop = face_crop[start_y:start_y + min_dim, start_x:start_x + min_dim]
        return cv2.resize(square_crop, self.output_size, interpolation=cv2.INTER_AREA)
