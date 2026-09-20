"""Interactive Webcam Enrollment Utility: Captures Front, Left, Right face photos for a new student."""
import cv2
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.face.detector import FaceDetector
from app.face.quality import FaceQualityAssessor
from app.enrollment.enroll import EnrollmentEngine

def main():
    print("=" * 60)
    print("     STUDENT BIOMETRIC ENROLLMENT STATION (WEBCAM)     ")
    print("=" * 60)
    student_id = input("Enter Student ID (e.g. STU001): ").strip()
    if not student_id:
        print("Student ID cannot be empty.")
        return

    name = input("Enter Student Name (e.g. Aashish Kumar): ").strip()
    department = input("Enter Department (default ECE): ").strip() or "ECE"

    save_dir = Path(f"data/students/{student_id}/raw_captures")
    save_dir.mkdir(parents=True, exist_ok=True)

    poses = ["FRONTAL", "SLIGHT LEFT", "SLIGHT RIGHT", "SLIGHT UP", "SMILE / EXPRESSION"]
    captured_paths = []

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    detector = FaceDetector()
    quality = FaceQualityAssessor()

    print("\nInstructions:")
    print("  - Look at the camera as prompted.")
    print("  - Press 'SPACEBAR' to capture each pose.")
    print("  - Press 'q' to cancel enrollment.\n")

    for idx, pose_name in enumerate(poses):
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            faces = detector.detect_in_frame(frame)

            status_color = (0, 255, 0)
            status_text = "READY - PRESS SPACE"
            usable = False

            if faces:
                best = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                x1, y1, x2, y2 = best.bbox
                report = quality.assess(best.crop)
                usable = report.is_usable

                box_color = (0, 255, 120) if usable else (0, 100, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(
                    frame,
                    f"Quality: {report.overall_reliability:.2f} (Blur: {report.sharpness_score:.2f})",
                    (x1, max(y1 - 10, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    box_color,
                    2
                )
                if not usable:
                    status_color = (0, 100, 255)
                    status_text = "POOR QUALITY - ADJUST LIGHT / DISTANCE"
            else:
                status_color = (0, 0, 255)
                status_text = "NO FACE DETECTED"

            # Top instructions banner
            cv2.rectangle(frame, (0, 0), (w, 65), (25, 25, 28), -1)
            cv2.putText(frame, f"POSE [{idx+1}/{len(poses)}]: {pose_name}", (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)
            cv2.putText(frame, status_text, (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2)

            cv2.imshow("Student Enrollment Station", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 32:  # SPACEBAR
                if usable and faces:
                    img_path = save_dir / f"capture_{idx+1}_{pose_name.replace(' ', '_').lower()}.jpg"
                    cv2.imwrite(str(img_path), frame)
                    captured_paths.append(str(img_path))
                    print(f"Captured {pose_name} -> {img_path.name}")
                    break
                else:
                    print("Cannot capture: face not detected or quality insufficient.")
            elif key == ord('q') or key == 27:
                print("Enrollment cancelled.")
                cap.release()
                cv2.destroyAllWindows()
                return

    cap.release()
    cv2.destroyAllWindows()

    print(f"\nProcessing {len(captured_paths)} captures through Enrollment Engine...")
    engine = EnrollmentEngine()
    success, msg = engine.enroll_student_from_images(
        student_id=student_id,
        name=name,
        department=department,
        image_paths=captured_paths
    )
    print(msg)

if __name__ == "__main__":
    main()
