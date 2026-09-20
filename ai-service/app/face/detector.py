"""High-speed CPU Face Detector supporting OpenCV Haar Cascades and DNN SSD."""
import cv2
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class FaceDetection:
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    crop: np.ndarray

class FaceDetector:
    def __init__(self, min_size: Tuple[int, int] = (40, 40)):
        self.min_size = min_size
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load OpenCV face cascade classifier.")

    def detect_in_frame(self, frame: np.ndarray) -> List[FaceDetection]:
        """Detects all faces in a whole frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=self.min_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        results = []
        for (x, y, w, h) in faces:
            x1, y1, x2, y2 = max(0, x), max(0, y), min(frame.shape[1], x + w), min(frame.shape[0], y + h)
            crop = frame[y1:y2, x1:x2]
            results.append(FaceDetection(
                bbox=(x1, y1, x2, y2),
                confidence=0.90,
                crop=crop
            ))
        return results

    def detect_in_person_crop(self, person_crop: np.ndarray, offset: Tuple[int, int] = (0, 0)) -> List[FaceDetection]:
        """Detects faces within the upper half/torso of a tracked person bounding box."""
        if person_crop is None or person_crop.size == 0:
            return []

        h, w = person_crop.shape[:2]
        # Focus on upper 60% of person box to reduce false positives
        upper_h = int(h * 0.65)
        upper_crop = person_crop[0:upper_h, :]

        gray = cv2.cvtColor(upper_crop, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(max(24, int(w * 0.15)), max(24, int(h * 0.12)))
        )

        ox, oy = offset
        results = []
        for (x, y, fw, fh) in faces:
            abs_x1 = ox + x
            abs_y1 = oy + y
            abs_x2 = ox + x + fw
            abs_y2 = oy + y + fh
            crop = upper_crop[y:y+fh, x:x+fw]
            results.append(FaceDetection(
                bbox=(abs_x1, abs_y1, abs_x2, abs_y2),
                confidence=0.92,
                crop=crop
            ))
        return results
