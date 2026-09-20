"""Week 3 Recognition Pipeline: Ingestion -> Tracking -> Face Detection -> FAISS -> Temporal Confirmation."""
import argparse
import sys
import os
import time
import threading
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.camera.source import VideoSource
from app.pipeline.frame_queue import FrameBuffer, BufferedFrame
from app.metrics.ingestion_metrics import IngestionMetrics
from app.tracking.tracker import ByteTrackTracker
from app.face.detector import FaceDetector
from app.face.quality import FaceQualityAssessor
from app.face.embedder import FaceEmbedder
from app.face.matcher import FaceMatcher
from app.identity.identity_manager import TemporalIdentityManager
from app.enrollment.registry import StudentRegistry

def build_recognition_hud(frame_w: int, metrics_data: dict) -> np.ndarray:
    hud_h = 160
    hud = np.zeros((hud_h, frame_w, 3), dtype=np.uint8)
    hud[:] = (20, 20, 24)

    cv2.line(hud, (0, 0), (frame_w, 0), (0, 220, 255), 2)
    cv2.putText(
        hud,
        "AI VIDEO ATTENDANCE — WEEK 3: TRACK IDENTITY RECOGNITION (FAISS)",
        (20, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 220, 255),
        2
    )

    col1_x = 25
    col2_x = max(frame_w // 2, 340)

    cv2.putText(hud, f"SOURCE       : {metrics_data['source_type']}", (col1_x, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"ENROLLED DB  : {metrics_data['enrolled_count']} students ({metrics_data['faiss_vectors']} vectors)", (col1_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"CONFIRMED    : {metrics_data['confirmed_count']} | TENTATIVE: {metrics_data['tentative_count']}", (col1_x, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 120), 2)

    cv2.putText(hud, f"INPUT FPS    : {metrics_data['input_fps']:.1f}", (col2_x, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"PIPELINE FPS : {metrics_data['pipe_fps']:.1f}  ({metrics_data['latency_ms']:.1f}ms)", (col2_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"ACTIVE TRACKS: {metrics_data['active_tracks']}  | Queue: {metrics_data['queue_size']}/{metrics_data['max_queue']}", (col2_x, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1)

    cv2.putText(hud, "Press 'q' or ESC to exit", (frame_w - 210, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (130, 130, 130), 1)
    return hud

def main():
    default_video = Path(__file__).resolve().parent.parent / "data" / "videos" / "pedestrians_sample.mp4"

    parser = argparse.ArgumentParser(description="AI Attendance - Week 3 Track-to-Face Recognition")
    parser.add_argument("--source", type=str, default="webcam", help="'webcam' (or 0) for laptop camera, or path to MP4 video")
    parser.add_argument("--no-display", action="store_true", help="Run without UI window")
    parser.add_argument("--max-frames", type=int, default=-1, help="Max frames to process")
    args = parser.parse_args()

    if args.source == "webcam" or args.source == "0":
        src_target = 0
        src_label = "LAPTOP WEBCAM"
    else:
        src_target = args.source if os.path.isabs(args.source) or os.path.exists(args.source) else str(default_video)
        src_label = f"VIDEO ({Path(src_target).name})"

    print("=" * 65)
    print("  AI VIDEO ATTENDANCE — WEEK 3 FACE RECOGNITION PIPELINE")
    print("=" * 65)
    print(f" Source      : {src_label} [{src_target}]")
    print("=" * 65)

    try:
        video_src = VideoSource(src_target, loop=True)
    except Exception as e:
        print(f"[ERROR] Failed to open video source: {e}")
        return

    buffer = FrameBuffer(max_size=30)
    metrics = IngestionMetrics(window_sec=3.0)
    
    # Initialize Pipeline Components
    tracker = ByteTrackTracker(model_name="yolov8n.pt", conf_thresh=0.35, device="cpu")
    face_detector = FaceDetector()
    quality_assessor = FaceQualityAssessor()
    embedder = FaceEmbedder(device="cpu")
    matcher = FaceMatcher()
    id_manager = TemporalIdentityManager(confirm_threshold=0.60, min_observations=2)
    registry = StudentRegistry()
    running = True

    def capture_worker():
        frame_counter = 0
        while running:
            ret, frame = video_src.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            frame_counter += 1
            now = time.perf_counter()
            metrics.record_input()

            pkt = BufferedFrame(
                frame_id=frame_counter,
                timestamp=now,
                frame=frame,
                source_name=src_label
            )
            buffer.put(pkt)

            if isinstance(src_target, str) and video_src.fps() > 0:
                time.sleep(1.0 / (video_src.fps() * 1.1))

    capture_thread = threading.Thread(target=capture_worker, name="CaptureWorker", daemon=True)
    capture_thread.start()

    consumed = 0
    display_w, display_h = 960, 540
    pipe_latency_ms = 0.0

    try:
        while running:
            pkt = buffer.get(timeout=0.05)
            now = time.perf_counter()

            if pkt is not None:
                orig_frame = pkt.frame
                start_proc = time.perf_counter()

                # Step 1: Track Persons
                tracks, track_lat = tracker.update(orig_frame)

                # Step 2: Selective Face Recognition on Active Tracks
                for t in tracks:
                    x1, y1, x2, y2 = t.bbox
                    h, w = orig_frame.shape[:2]
                    person_crop = orig_frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                    # Face Detection within Person Bounding Box
                    faces = face_detector.detect_in_person_crop(person_crop, offset=(x1, y1))
                    
                    matched_id = None
                    similarity = 0.0
                    reliability = 0.0

                    if faces:
                        # Select most prominent face in upper torso
                        best_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                        fx1, fy1, fx2, fy2 = best_face.bbox
                        cv2.rectangle(orig_frame, (fx1, fy1), (fx2, fy2), (255, 200, 0), 2)

                        # Assess Face Quality
                        quality_report = quality_assessor.assess(best_face.crop)
                        reliability = quality_report.overall_reliability

                        if quality_report.is_usable:
                            emb = embedder.extract(best_face.crop)
                            matches = matcher.search(emb, top_k=1)
                            if matches:
                                matched_id = matches[0].student_id
                                similarity = matches[0].similarity

                    # Update Temporal Identity State Machine
                    decision = id_manager.update_track_evidence(
                        track_id=t.track_id,
                        candidate_id=matched_id,
                        similarity=similarity,
                        reliability=reliability
                    )

                    # Badge color based on state
                    if decision.state == "CONFIRMED":
                        badge_color = (0, 255, 100)  # Green
                        stud_name = registry.get(decision.student_id).name if registry.get(decision.student_id) else decision.student_id
                        label = f"ID:{t.track_id} | {decision.student_id} ({stud_name}) | CONFIRMED"
                    elif decision.state == "TENTATIVE":
                        badge_color = (0, 200, 255)  # Yellow
                        label = f"ID:{t.track_id} | {decision.student_id or 'Searching'} | TENTATIVE"
                    else:
                        badge_color = (180, 180, 180) # Gray
                        label = f"ID:{t.track_id} | UNKNOWN"

                    cv2.rectangle(orig_frame, (x1, y1), (x2, y2), badge_color, 2)
                    cv2.putText(
                        orig_frame,
                        label,
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        badge_color,
                        2
                    )

                pipe_latency_ms = (time.perf_counter() - start_proc) * 1000.0
                metrics.record_processed(pipe_latency_ms)
                consumed += 1
                frame_to_show = orig_frame
            else:
                frame_to_show = np.zeros((display_h, display_w, 3), dtype=np.uint8)

            resized_frame = cv2.resize(frame_to_show, (display_w, display_h))

            # Count confirmed/tentative states
            confirmed_count = sum(1 for d in id_manager.current_decisions.values() if d.state == "CONFIRMED")
            tentative_count = sum(1 for d in id_manager.current_decisions.values() if d.state == "TENTATIVE")

            metrics_payload = {
                "source_type": src_label,
                "enrolled_count": len(registry.students),
                "faiss_vectors": matcher.index.ntotal,
                "confirmed_count": confirmed_count,
                "tentative_count": tentative_count,
                "active_tracks": len(tracker.trajectory_history),
                "input_fps": metrics.input_fps,
                "pipe_fps": metrics.process_fps,
                "latency_ms": pipe_latency_ms,
                "queue_size": buffer.size(),
                "max_queue": buffer.max_size,
                "dropped": buffer.dropped_frames,
            }

            hud = build_recognition_hud(display_w, metrics_payload)
            canvas = np.vstack([resized_frame, hud])

            if not args.no_display:
                cv2.imshow("AI Attendance - Week 3 Face Recognition", canvas)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break

            if args.max_frames > 0 and consumed >= args.max_frames:
                break

    finally:
        running = False
        capture_thread.join(timeout=1.0)
        video_src.release()
        if not args.no_display:
            cv2.destroyAllWindows()
        print(f"Recognition pipeline stopped. Total processed frames: {consumed}")

if __name__ == "__main__":
    main()
