"""Student Body Gallery Manager: Registers full-body crops and indexes embeddings."""
from pathlib import Path
from typing import List, Tuple
import cv2

from app.reid.extractor import BodyEmbedder
from app.reid.quality import BodyQualityAssessor
from app.reid.matcher import BodyMatcher

class BodyGalleryManager:
    def __init__(self):
        self.embedder = BodyEmbedder()
        self.quality = BodyQualityAssessor()
        self.matcher = BodyMatcher()

    def enroll_student_body(self, student_id: str, body_image_paths: List[str]) -> Tuple[int, str]:
        saved = 0
        sdir = Path(f"data/students/{student_id}/body")
        sdir.mkdir(parents=True, exist_ok=True)

        for p in body_image_paths:
            img = cv2.imread(str(p))
            if img is None:
                continue

            report = self.quality.assess(img)
            if not report.is_usable:
                print(f"[BodyGallery] Body crop rejected ({p}): reliability={report.overall_reliability:.2f}")
                continue

            emb = self.embedder.extract(img)
            self.matcher.add_embedding(student_id, emb)

            out_crop = sdir / f"body_{saved + 1:02d}.jpg"
            cv2.imwrite(str(out_crop), img)
            saved += 1

        return saved, f"Enrolled {saved} body representations for {student_id}."
