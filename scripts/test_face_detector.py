"""Step 5 Standalone Test: Face Detection on Webcam or Video without recognition."""
import cv2
import time
import argparse
import sys
import os

sys.path.insert(0, os.path.abspath("ai-service"))
from app.face.detector import FaceDetector

def main():
    parser = argparse.ArgumentParser(description="Standalone Face Detection Test")
    parser.add_argument("--source", type=str, default="0", help="Camera index or video path")
    args = parser.parse_args()

    src = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video source: {src}")
        return

    detector = FaceDetector()
    print("Running Face Detection... Press 'q' or ESC to exit.")

    frame_count = 0
    start = time.perf_counter()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        faces = detector.detect_in_frame(frame)

        for f in faces:
            x1, y1, x2, y2 = f.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 120), 2)
            w, h = x2 - x1, y2 - y1
            cv2.putText(
                frame,
                f"FACE: {w}x{h} | Conf: {f.confidence:.2f}",
                (x1, max(y1 - 10, 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 120),
                2
            )

        elapsed = time.perf_counter() - start
        fps = frame_count / elapsed if elapsed > 0 else 0

        # Info Box
        cv2.rectangle(frame, (15, 15), (320, 110), (20, 20, 24), -1)
        cv2.putText(frame, "FACE DETECTION TEST", (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
        cv2.putText(frame, f"FPS       : {fps:.1f}", (25, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"FACES SEEN: {len(faces)}", (25, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 2)

        cv2.imshow("Face Detection Standalone", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
