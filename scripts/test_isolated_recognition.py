"""Step 10 Verification: Tests recognition in isolation without CCTV (Known, Unknown, Variation)."""
import sys
import os
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath("ai-service"))

from app.face.detector import FaceDetector
from app.face.quality import FaceQualityAssessor
from app.face.embedder import FaceEmbedder
from app.face.matcher import FaceMatcher
from app.enrollment.registry import StudentRegistry

def run_isolated_tests():
    print("=" * 60)
    print(" STEP 10: STANDALONE FACE RECOGNITION VALIDATION TEST")
    print("=" * 60)

    detector = FaceDetector()
    quality = FaceQualityAssessor()
    embedder = FaceEmbedder(device="cpu")
    matcher = FaceMatcher()
    registry = StudentRegistry()

    SIMILARITY_THRESHOLD = 0.50

    def evaluate_image(label: str, img_path: str, expected_id: str = None):
        print(f"\n--- {label} ({img_path}) ---")
        img = cv2.imread(img_path)
        if img is None:
            print("  [ERROR] Image not found.")
            return

        faces = detector.detect_in_frame(img)
        if not faces:
            print("  No face detected.")
            return

        best = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
        report = quality.assess(best.crop)
        print(f"  Face Detected: {best.bbox} | Overall Quality: {report.overall_reliability:.2f} (Sharpness: {report.sharpness_score:.2f})")

        emb = embedder.extract(best.crop)
        matches = matcher.search(emb, top_k=2)

        if not matches:
            decision = "UNKNOWN"
            score = 0.0
        else:
            top_match = matches[0]
            score = top_match.similarity
            if score >= SIMILARITY_THRESHOLD:
                decision = top_match.student_id
            else:
                decision = "UNKNOWN (Below threshold)"

        student_info = registry.get(decision).name if registry.get(decision) else "N/A"
        print(f"  Top Match ID : {matches[0].student_id if matches else 'None'} (Score: {score:.4f})")
        print(f"  Decision     : {decision} [{student_info}]")
        print(f"  Status       : {'PASS' if (expected_id == decision or (expected_id is None and 'UNKNOWN' in decision)) else 'CHECK'}")

    # Test A: Known enrolled person STU001
    evaluate_image("Test A: Enrolled Student STU001", "data/students/STU001/raw_captures/face_01.jpg", expected_id="STU001")

    # Test B: Different enrolled student STU002
    evaluate_image("Test B: Enrolled Student STU002", "data/students/STU002/raw_captures/face_01.jpg", expected_id="STU002")

    # Test C: Photo variation of STU001
    evaluate_image("Test C: Pose Variation STU001", "data/students/STU001/raw_captures/pose_01.jpg", expected_id="STU001")

    # Test D: Unknown person synthetic dummy
    unknown_img = np.zeros((240, 240, 3), dtype=np.uint8)
    unknown_img[:] = (200, 200, 200)
    cv2.circle(unknown_img, (120, 120), 60, (50, 50, 50), -1)
    cv2.imwrite("data/students/unknown_dummy.jpg", unknown_img)
    evaluate_image("Test D: Unknown / Non-face Pattern", "data/students/unknown_dummy.jpg", expected_id=None)

    print("\n" + "=" * 60)
    print(" Isolated recognition test complete.")
    print("=" * 60)

if __name__ == "__main__":
    run_isolated_tests()
