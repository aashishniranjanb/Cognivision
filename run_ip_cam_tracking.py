"""Standalone Live Camera & IP Cam Face Tracking Script.
Connects directly to your IP Camera (http://192.168.1.3:8080/video) or iVCam/Webcam,
detects faces, matches against enrolled students (STU001 - Aashish Kumar),
renders a real-time HUD with tracking boxes, and posts attendance events to Spring Boot.
"""
import sys
import os
import time
import argparse
from pathlib import Path
import cv2
import numpy as np

# Ensure ai-service root in path
sys.path.insert(0, os.path.abspath("ai-service"))

from app.face.detector import FaceDetector
from app.face.embedder import FaceEmbedder
from app.face.matcher import FaceMatcher
from app.enrollment.registry import StudentRegistry
from app.events.event_schema import CampusEvent
from app.integration.spring_backend_adapter import default_spring_adapter

def main():
    parser = argparse.ArgumentParser(description="Live IP Camera Face Tracking & Attendance")
    parser.add_argument("--url", default="http://192.168.1.3:8080/video", help="IP camera stream URL (default: http://192.168.1.3:8080/video)")
    parser.add_argument("--cam", type=int, default=None, help="Local webcam device index (e.g. 0 or 1)")
    parser.add_argument("--threshold", type=float, default=0.40, help="Cosine similarity match threshold (default: 0.40)")
    args = parser.parse_args()

    print("=" * 70)
    print(" SRM AI ATTENDANCE — LIVE IP CAMERA TRACKING ENGINE")
    print("=" * 70)

    # 1. Initialize biometrics
    detector = FaceDetector()
    embedder = FaceEmbedder()
    matcher = FaceMatcher()
    registry = StudentRegistry()

    print(f"[Matcher] FAISS Index contains {matcher.index.ntotal} registered face vectors.")
    print(f"[Registry] Enrolled students: {list(registry.students.keys())}")

    # 2. Open camera source
    source_target = args.cam if args.cam is not None else args.url
    print(f"\n[Camera] Connecting to: {source_target} ...")

    cap = cv2.VideoCapture(source_target)
    if not cap.isOpened() and args.cam is None:
        print(f"[Camera] Failed to open {source_target}. Falling back to default webcam (device 0)...")
        cap = cv2.VideoCapture(0)
        source_target = "Webcam 0"

    if not cap.isOpened():
        print("[ERROR] Could not open any camera device. Check your IP cam connection or webcam.")
        return

    print(f"[Camera] Connected successfully to: {source_target}")
    print("[Instructions] Position your face or show the student photo to the camera.")
    print("Press 'q' or ESC in the window to exit.\n")

    last_event_time = {}
    fps_time = time.perf_counter()
    fps_counter = 0
    display_fps = 0.0

    cv2.namedWindow("SRM AI Live Tracking - CAM01", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("SRM AI Live Tracking - CAM01", 960, 540)

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            fps_counter += 1
            now = time.perf_counter()
            if now - fps_time >= 1.0:
                display_fps = fps_counter / (now - fps_time)
                fps_counter = 0
                fps_time = now

            h, w = frame.shape[:2]

            # Detect faces
            faces = detector.detect_in_frame(frame)
            active_matches = []

            for f in faces:
                fx1, fy1, fx2, fy2 = f.bbox
                emb = embedder.extract(f.crop)
                matches = matcher.search(emb, top_k=1)

                student_id = "UNKNOWN"
                student_name = "Unregistered"
                similarity = 0.0
                is_confirmed = False

                if matches:
                    top = matches[0]
                    similarity = top.similarity
                    if similarity >= args.threshold:
                        student_id = top.student_id
                        rec = registry.get(student_id)
                        student_name = rec.name if rec else student_id
                        is_confirmed = True

                        # Debounced Attendance Dispatch (> 5 sec)
                        now_sec = time.time()
                        if now_sec - last_event_time.get(student_id, 0) > 5.0:
                            last_event_time[student_id] = now_sec
                            evt = CampusEvent.create_attendance(
                                student_id=student_id,
                                camera_id="CAM01",
                                classroom_id="CLASSROOM_101",
                                track_id=101 + len(active_matches),
                                direction="IN",
                                confidence=round(float(similarity), 2)
                            )
                            # Dispatch directly to Spring Boot backend!
                            dispatched = default_spring_adapter.forward_event(evt)
                            print(f"[ATTENDANCE] Marked {student_id} ({student_name}) | Sim: {similarity:.2f} | Spring Backend Dispatched: {dispatched}")

                active_matches.append({
                    "bbox": (fx1, fy1, fx2, fy2),
                    "student_id": student_id,
                    "student_name": student_name,
                    "similarity": similarity,
                    "is_confirmed": is_confirmed
                })

            # Render Overlays
            for m in active_matches:
                fx1, fy1, fx2, fy2 = m["bbox"]
                fw, fh = fx2 - fx1, fy2 - fy1
                color = (0, 230, 115) if m["is_confirmed"] else (0, 140, 255)

                # Expanded body box
                px1 = max(0, fx1 - int(fw * 0.4))
                px2 = min(w, fx2 + int(fw * 0.4))
                py1 = max(0, fy1 - int(fh * 0.2))
                py2 = min(h, fy2 + int(fh * 2.5))
                cv2.rectangle(frame, (px1, py1), (px2, py2), color, 1)

                # Face Box
                cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), color, 2)

                # Corner brackets
                clen = 15
                cv2.line(frame, (fx1, fy1), (fx1 + clen, fy1), color, 3)
                cv2.line(frame, (fx1, fy1), (fx1, fy1 + clen), color, 3)
                cv2.line(frame, (fx2, fy1), (fx2 - clen, fy1), color, 3)
                cv2.line(frame, (fx2, fy1), (fx2, fy1 + clen), color, 3)
                cv2.line(frame, (fx1, fy2), (fx1 + clen, fy2), color, 3)
                cv2.line(frame, (fx1, fy2), (fx1, fy2 - clen), color, 3)
                cv2.line(frame, (fx2, fy2), (fx2 - clen, fy2), color, 3)
                cv2.line(frame, (fx2, fy2), (fx2, fy2 - clen), color, 3)

                # Label Pill
                pct = int(m["similarity"] * 100)
                if m["is_confirmed"]:
                    label_txt = f"{m['student_id']}: {m['student_name']} ({pct}%)"
                else:
                    label_txt = f"UNKNOWN ({pct}%)"

                (lw, lh), _ = cv2.getTextSize(label_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                by1 = max(0, fy1 - 25)
                cv2.rectangle(frame, (fx1, by1), (fx1 + lw + 14, fy1), color, -1)
                cv2.putText(frame, label_txt, (fx1 + 7, fy1 - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

            # Virtual Entry Line
            mid_y = int(h * 0.60)
            cv2.line(frame, (40, mid_y), (w - 40, mid_y), (0, 255, 0), 2)
            cv2.putText(frame, "ENTRY BOUNDARY LINE", (50, mid_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

            # Top Header Bar
            cv2.rectangle(frame, (0, 0), (w, 42), (20, 20, 24), -1)
            cv2.line(frame, (0, 42), (w, 42), (0, 220, 255), 2)
            hud_text = f"SRM CCTV [CAM01] | SRC: {source_target} | {display_fps:.1f} FPS | {time.strftime('%H:%M:%S')}"
            cv2.putText(frame, hud_text, (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 1)

            if active_matches:
                cv2.putText(frame, f"IDENTIFIED: {len(active_matches)}", (w - 180, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 120), 2)

            cv2.imshow("SRM AI Live Tracking - CAM01", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\n[Camera] Stream stopped cleanly.")

if __name__ == "__main__":
    main()
