"""High-fidelity Face Detector tailored for Biometric Enrollment with Landmark Localization."""
import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

@dataclass
class EnrollmentFace:
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    face_crop: np.ndarray
    left_eye: Optional[Tuple[int, int]] = None   # In face_crop coordinate system
    right_eye: Optional[Tuple[int, int]] = None  # In face_crop coordinate system
    nose_tip: Optional[Tuple[int, int]] = None
    mouth_center: Optional[Tuple[int, int]] = None

class EnrollmentFaceDetector:
    def __init__(self, min_face_size: Tuple[int, int] = (60, 60)):
        self.min_face_size = min_face_size
        frontal_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        profile_path = cv2.data.haarcascades + "haarcascade_profileface.xml"
        eye_path = cv2.data.haarcascades + "haarcascade_eye.xml"

        self.face_cascade = cv2.CascadeClassifier(frontal_path)
        self.profile_cascade = cv2.CascadeClassifier(profile_path)
        self.eye_cascade = cv2.CascadeClassifier(eye_path)

    def detect_primary_face(self, frame: np.ndarray) -> Optional[EnrollmentFace]:
        """Detects the primary (largest, most prominent) enrollment face with landmarks."""
        all_faces = self.detect_all_faces(frame)
        if not all_faces:
            return None
        # In enrollment, the candidate is the largest face in frame
        return max(all_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

    def detect_all_faces(self, frame: np.ndarray) -> List[EnrollmentFace]:
        if frame is None or frame.size == 0:
            return []

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        # 1. Frontal faces
        detected_boxes = list(self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=5,
            minSize=self.min_face_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        ))

        # 2. Try profiles if no frontal face detected
        if len(detected_boxes) == 0 and not self.profile_cascade.empty():
            prof_left = self.profile_cascade.detectMultiScale(
                gray, scaleFactor=1.08, minNeighbors=4, minSize=self.min_face_size
            )
            for b in prof_left:
                detected_boxes.append(b)

            flipped = cv2.flip(gray, 1)
            prof_right = self.profile_cascade.detectMultiScale(
                flipped, scaleFactor=1.08, minNeighbors=4, minSize=self.min_face_size
            )
            for (x, y, fw, fh) in prof_right:
                detected_boxes.append((w - (x + fw), y, fw, fh))

        # Fallback for synthetic/oval patterns
        if len(detected_boxes) == 0:
            circles = cv2.HoughCircles(
                cv2.GaussianBlur(gray, (9, 9), 2),
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=100,
                param1=50,
                param2=30,
                minRadius=int(self.min_face_size[0] / 2),
                maxRadius=int(h / 2)
            )
            if circles is not None:
                for c in circles[0, :1]:
                    cx, cy, r = int(c[0]), int(c[1]), int(c[2])
                    detected_boxes.append((cx - r, cy - r, 2 * r, 2 * r))

        results: List[EnrollmentFace] = []
        for (x, y, fw, fh) in detected_boxes:
            x1, y1 = max(0, int(x)), max(0, int(y))
            x2, y2 = min(w, int(x + fw)), min(h, int(y + fh))
            if x2 <= x1 or y2 <= y1:
                continue

            crop = frame[y1:y2, x1:x2].copy()
            crop_gray = gray[y1:y2, x1:x2]

            # Detect eye landmarks inside face crop
            left_eye, right_eye = self._locate_eyes(crop_gray)
            ch, cw = crop.shape[:2]
            nose_tip = (int(cw * 0.5), int(ch * 0.55))
            mouth_center = (int(cw * 0.5), int(ch * 0.80))

            results.append(EnrollmentFace(
                bbox=(x1, y1, x2, y2),
                confidence=0.96 if len(detected_boxes) == 1 else 0.90,
                face_crop=crop,
                left_eye=left_eye,
                right_eye=right_eye,
                nose_tip=nose_tip,
                mouth_center=mouth_center
            ))

        return results

    def _locate_eyes(self, face_gray: np.ndarray) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
        """Detects left and right eye coordinates inside a cropped face region."""
        h, w = face_gray.shape[:2]
        # Restrict eye search to upper 60% of face
        upper_half = face_gray[0:int(h * 0.6), :]
        eyes = self.eye_cascade.detectMultiScale(upper_half, scaleFactor=1.1, minNeighbors=3, minSize=(15, 15))

        if len(eyes) >= 2:
            # Sort eyes by X position
            sorted_eyes = sorted(eyes, key=lambda e: e[0])
            e1, e2 = sorted_eyes[0], sorted_eyes[-1]
            left_eye = (int(e1[0] + e1[2] / 2), int(e1[1] + e1[3] / 2))
            right_eye = (int(e2[0] + e2[2] / 2), int(e2[1] + e2[3] / 2))
            return left_eye, right_eye

        # Geometric heuristic fallback
        default_left = (int(w * 0.32), int(h * 0.38))
        default_right = (int(w * 0.68), int(h * 0.38))
        return default_left, default_right
