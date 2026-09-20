"""Week 2 Day 1 Pipeline: Ingestion -> Buffer -> YOLO Person Detector -> HUD & BBoxes."""
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
from app.detection.detector import PersonDetector

def build_detection_hud(frame_w: int, metrics_data: dict) -> np.ndarray:
    hud_h = 160
    hud = np.zeros((hud_h, frame_w, 3), dtype=np.uint8)
    hud[:] = (20, 20, 24)

    cv2.line(hud, (0, 0), (frame_w, 0), (0, 220, 255), 2)
    cv2.putText(
        hud,
        "AI VIDEO ATTENDANCE — WEEK 2: PERSON DETECTION",
        (20, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 220, 255),
        2
    )

    col1_x = 25
    col2_x = max(frame_w // 2, 340)

    cv2.putText(hud, f"SOURCE       : {metrics_data['source_type']}", (col1_x, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"RESOLUTION   : {metrics_data['resolution']}", (col1_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"PEOPLE COUNT : {metrics_data['people_count']} detected", (col1_x, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 120), 2)

    cv2.putText(hud, f"INPUT FPS    : {metrics_data['input_fps']:.1f}", (col2_x, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"DETECTION FPS: {metrics_data['detection_fps']:.1f}  ({metrics_data['det_latency_ms']:.1f}ms)", (col2_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"QUEUE BUFFER : {metrics_data['queue_size']} / {metrics_data['max_queue']}  (Dropped: {metrics_data['dropped']})", (col2_x, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1)

    cv2.putText(hud, "Press 'q' or ESC to exit", (frame_w - 210, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (130, 130, 130), 1)
    return hud


def main():
    default_video = Path(__file__).resolve().parent.parent / "data" / "videos" / "test_video.mp4"

    parser = argparse.ArgumentParser(description="AI Video Attendance - Week 2 Person Detection")
    parser.add_argument("--source", type=str, default="webcam", help="'webcam' (or 0) for laptop camera, or path to MP4 video")
    parser.add_argument("--conf", type=float, default=0.45, help="Confidence threshold for person detector")
    parser.add_argument("--no-display", action="store_true", help="Run without UI window")
    parser.add_argument("--max-frames", type=int, default=-1, help="Max frames to process")
    args = parser.parse_args()

    if args.source == "webcam" or args.source == "0":
        src_target = 0
        src_label = "LAPTOP WEBCAM"
    else:
        src_target = args.source if os.path.isabs(args.source) or os.path.exists(args.source) else str(default_video)
        src_label = f"VIDEO ({Path(src_target).name})"

    print("=" * 60)
    print("  AI VIDEO ATTENDANCE — WEEK 2 PERSON DETECTION ENGINE")
    print("=" * 60)
    print(f" Source      : {src_label} [{src_target}]")
    print(f" Target Class: 'person' only (COCO class 0)")
    print(f" Confidence  : >= {args.conf}")
    print("=" * 60)

    try:
        video_src = VideoSource(src_target, loop=True)
    except Exception as e:
        print(f"[ERROR] Failed to open video source: {e}")
        return

    buffer = FrameBuffer(max_size=30)
    metrics = IngestionMetrics(window_sec=3.0)
    detector = PersonDetector(model_name="yolov8n.pt", conf_thresh=args.conf, device="cpu")
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
    det_latency_ms = 0.0

    try:
        while running:
            pkt = buffer.get(timeout=0.05)
            now = time.perf_counter()

            if pkt is not None:
                orig_frame = pkt.frame
                detections, det_latency_ms = detector.detect(orig_frame)
                metrics.record_processed(det_latency_ms)
                consumed += 1

                # Draw person bounding boxes
                for det in detections:
                    x1, y1, x2, y2 = det.bbox
                    cv2.rectangle(orig_frame, (x1, y1), (x2, y2), (0, 255, 120), 2)
                    label = f"PERSON {det.confidence:.2f}"
                    cv2.putText(
                        orig_frame,
                        label,
                        (x1, max(y1 - 8, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 120),
                        2
                    )

                people_count = len(detections)
                frame_to_show = orig_frame
            else:
                frame_to_show = np.zeros((display_h, display_w, 3), dtype=np.uint8)
                people_count = 0

            resized_frame = cv2.resize(frame_to_show, (display_w, display_h))

            metrics_payload = {
                "source_type": src_label,
                "resolution": f"{video_src.width()} x {video_src.height()}",
                "people_count": people_count,
                "input_fps": metrics.input_fps,
                "detection_fps": metrics.process_fps,
                "det_latency_ms": det_latency_ms,
                "queue_size": buffer.size(),
                "max_queue": buffer.max_size,
                "dropped": buffer.dropped_frames,
            }

            hud = build_detection_hud(display_w, metrics_payload)
            canvas = np.vstack([resized_frame, hud])

            if not args.no_display:
                cv2.imshow("AI Attendance - Week 2 Detection", canvas)
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
        print(f"Detection pipeline stopped. Total processed frames: {consumed}")

if __name__ == "__main__":
    main()
