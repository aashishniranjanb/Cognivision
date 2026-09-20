"""Student Enrollment Engine: Processes multiple face images, validates quality, and registers in FAISS."""
import os
import cv2
from pathlib import Path
from typing import List, Tuple
from app.enrollment.registry import StudentRegistry
from app.face.detector import FaceDetector
from app.face.quality import FaceQualityAssessor
from app.face.embedder import FaceEmbedder
from app.face.matcher import FaceMatcher

class EnrollmentEngine:
    def __init__(self):
        self.registry = StudentRegistry()
        self.detector = FaceDetector()
        self.quality_assessor = FaceQualityAssessor()
        self.embedder = FaceEmbedder()
        self.matcher = FaceMatcher()

    def enroll_student_from_images(
        self,
        student_id: str,
        name: str,
        department: str,
        image_paths: List[str]
    ) -> Tuple[bool, str]:
        if not image_paths:
            return False, "No images provided for enrollment."

        # Register metadata in students.json
        student_rec = self.registry.register(student_id=student_id, name=name, department=department)

        saved_crops = 0
        student_dir = Path("data/students") / student_id
        student_dir.mkdir(parents=True, exist_ok=True)

        for p in image_paths:
            img = cv2.imread(str(p))
            if img is None:
                continue

            faces = self.detector.detect_in_frame(img)
            if not faces:
                print(f"[Enrollment] No face detected in: {p}")
                continue

            # Pick largest/most prominent face
            best_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            report = self.quality_assessor.assess(best_face.crop)

            if not report.is_usable:
                print(f"[Enrollment] Face quality rejected ({p}): reliability={report.overall_reliability:.2f}, blur={report.sharpness_score:.2f}")
                continue

            # Extract 512-d embedding
            embedding = self.embedder.extract(best_face.crop)
            self.matcher.add_embedding(student_id=student_id, embedding=embedding)

            crop_file = student_dir / f"face_{saved_crops + 1:02d}.jpg"
            cv2.imwrite(str(crop_file), best_face.crop)
            saved_crops += 1

        student_rec.embedding_count += saved_crops
        self.registry.save()

        if saved_crops == 0:
            return False, f"Enrollment failed: All {len(image_paths)} images failed face detection or quality checks."

        return True, f"Successfully enrolled {name} ({student_id}) with {saved_crops} valid face vectors."
