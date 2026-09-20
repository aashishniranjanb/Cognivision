"""CLI Student Enrollment script: Captures 5 face photos with real-time quality feedback and registers in FAISS."""
import argparse
import sys
import os
import time
import cv2
from pathlib import Path

sys.path.insert(0, os.path.abspath("ai-service"))

from app.face.detector import FaceDetector
from app.face.quality import FaceQualityAssessor
from app.enrollment.enroll import EnrollmentEngine

def enroll_student_interactive(student_id: str, name: str, department: str = "ECE", year: int = 4):
    print("=" * 60)
    print("             STUDENT BIOMETRIC ENROLLMENT               ")
    print("=" * 60)
    print(f" Student ID : {student_id}")
    print(f" Name       : {name}")
    print(f" Department : {department} (Year {year})")
    print("=" * 60)

    save_dir = Path(f"data/students/{student_id}/raw_captures")
    save_dir.mkdir(parents=True, exist_ok=True)

    poses = [
        "Photo 1: Straight toward camera",
        "Photo 2: Slightly left",
        "Photo 3: Slightly right",
        "Photo 4: Different facial expression",
        "Photo 5: Slightly different lighting / distance"
    ]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return False

    detector = FaceDetector()
    quality_assessor = FaceQualityAssessor()
    captured_files = []

    print("\nPress 'SPACEBAR' when green box indicates acceptable face quality.")
    print("Press 'q' to cancel.\n")

    for idx, prompt in enumerate(poses):
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            faces = detector.detect_in_frame(frame)

            status_text = "POSITION FACE IN FRAME"
            status_color = (0, 0, 255)
            is_valid = False

            if faces:
                best_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                x1, y1, x2, y2 = best_face.bbox
                report = quality_assessor.assess(best_face.crop)
                is_valid = report.is_usable

                box_color = (0, 255, 120) if is_valid else (0, 140, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

                q_label = f"Quality: {report.overall_reliability:.2f} | Blur: {report.sharpness_score:.2f}"
                cv2.putText(frame, q_label, (x1, max(y1 - 10, 25)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, box_color, 2)

                if is_valid:
                    status_text = "READY - PRESS SPACE"
                    status_color = (0, 255, 120)
                else:
                    status_text = "LOW QUALITY - INCREASE LIGHT OR FACE CAMERA"
                    status_color = (0, 140, 255)

            # Header Banner
            cv2.rectangle(frame, (0, 0), (w, 75), (20, 20, 24), -1)
            cv2.putText(frame, f"ENROLLING: {name} ({student_id})", (20, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2)
            cv2.putText(frame, f"[{idx+1}/5] {prompt}", (20, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
            cv2.putText(frame, status_text, (20, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.48, status_color, 2)

            cv2.imshow("Student Enrollment", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 32:  # SPACEBAR
                if is_valid and faces:
                    out_path = save_dir / f"face_{idx+1:02d}.jpg"
                    cv2.imwrite(str(out_path), frame)
                    captured_files.append(str(out_path))
                    print(f"[{idx+1}/5] Face captured. Quality: {report.overall_reliability:.2f} -> Saved.")
                    break
                else:
                    print("Cannot capture: Face not detected or quality insufficient.")
            elif key == ord('q') or key == 27:
                print("Enrollment aborted by user.")
                cap.release()
                cv2.destroyAllWindows()
                return False

    cap.release()
    cv2.destroyAllWindows()

    print("\nGenerating identity embeddings and updating FAISS index...")
    engine = EnrollmentEngine()
    success, msg = engine.enroll_student_from_images(
        student_id=student_id,
        name=name,
        department=department,
        image_paths=captured_files
    )
    print(msg)
    return success

def main():
    parser = argparse.ArgumentParser(description="Enroll a student via webcam")
    parser.add_argument("--student-id", type=str, required=True, help="Unique student ID (e.g. STU001)")
    parser.add_argument("--name", type=str, required=True, help="Student full name")
    parser.add_argument("--department", type=str, default="ECE", help="Department")
    parser.add_argument("--year", type=int, default=4, help="Year of study")
    args = parser.parse_args()

    enroll_student_interactive(
        student_id=args.student_id,
        name=args.name,
        department=args.department,
        year=args.year
    )

if __name__ == "__main__":
    main()
