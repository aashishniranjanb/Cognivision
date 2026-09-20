"""Week 2 Tracking Pipeline: Ingestion -> Buffer -> YOLOv8n + ByteTrack -> Persistent IDs HUD."""
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

# Color palette for persistent track bounding boxes
TRACK_COLORS = [
    (0, 255, 120),    # Bright Green
    (255, 140, 0),    # Amber
    (0, 180, 255),    # Cyan/Orange
    (255, 50, 180),   # Magenta
    (50, 220, 255),   # Yellow-Cyan
    (180, 100, 255),  # Purple
    (255, 220, 50),   # Gold
]

def build_tracking_hud(frame_w: int, metrics_data: dict) -> np.ndarray:
    hud_h = 160
    hud = np.zeros((hud_h, frame_w, 3), dtype=np.uint8)
    hud[:] = (20, 20, 24)

    cv2.line(hud, (0, 0), (frame_w, 0), (0, 220, 255), 2)
    cv2.putText(
        hud,
        "AI VIDEO ATTENDANCE — WEEK 2: MULTI-OBJECT TRACKING (BYTETRACK)",
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
    cv2.putText(hud, f"ACTIVE TRACKS: {metrics_data['active_tracks']}  (Total Seen: {metrics_data['total_seen']})", (col1_x, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 120), 2)

    cv2.putText(hud, f"INPUT FPS    : {metrics_data['input_fps']:.1f}", (col2_x, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"TRACKING FPS : {metrics_data['tracking_fps']:.1f}  (Latency: {metrics_data['track_latency_ms']:.1f}ms)", (col2_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"QUEUE BUFFER : {metrics_data['queue_size']} / {metrics_data['max_queue']}  (Dropped: {metrics_data['dropped']})", (col2_x, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1)

    cv2.putText(hud, "Press 'q' or ESC to exit", (frame_w - 210, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (130, 130, 130), 1)
    return hud


def main():
    default_video = Path(__file__).resolve().parent.parent / "data" / "videos" / "pedestrians_sample.mp4"

    parser = argparse.ArgumentParser(description="AI Video Attendance - Week 2 Multi-Object Tracking")
    parser.add_argument("--source", type=str, default="video", help="'webcam' (or 0) for laptop camera, or path to MP4 video")
    parser.add_argument("--conf", type=float, default=0.35, help="Detection confidence threshold")
    parser.add_argument("--no-display", action="store_true", help="Run headless without preview")
    parser.add_argument("--max-frames", type=int, default=-1, help="Max frames to process")
    args = parser.parse_args()

    if args.source == "webcam" or args.source == "0":
        src_target = 0
        src_label = "LAPTOP WEBCAM"
    else:
        if args.source == "video" or not os.path.exists(args.source):
            src_target = str(default_video)
        else:
            src_target = args.source
        src_label = f"VIDEO ({Path(src_target).name})"

    print("=" * 65)
    print("  AI VIDEO ATTENDANCE — WEEK 2 MULTI-OBJECT TRACKING ENGINE")
    print("=" * 65)
    print(f" Source      : {src_label} [{src_target}]")
    print(f" Tracker     : ByteTrack (YOLOv8n + Kalman Filter Association)")
    print(f" Confidence  : >= {args.conf}")
    print("=" * 65)

    try:
        video_src = VideoSource(src_target, loop=True)
    except Exception as e:
        print(f"[ERROR] Failed to open video source: {e}")
        return

    buffer = FrameBuffer(max_size=30)
    metrics = IngestionMetrics(window_sec=3.0)
    tracker = ByteTrackTracker(model_name="yolov8n.pt", conf_thresh=args.conf, device="cpu")
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
    track_latency_ms = 0.0

    try:
        while running:
            pkt = buffer.get(timeout=0.05)
            now = time.perf_counter()

            if pkt is not None:
                orig_frame = pkt.frame
                tracks, track_latency_ms = tracker.update(orig_frame)
                metrics.record_processed(track_latency_ms)
                consumed += 1

                # Render persistent track boxes and trajectories
                for t in tracks:
                    color = TRACK_COLORS[t.track_id % len(TRACK_COLORS)]
                    x1, y1, x2, y2 = t.bbox
                    cv2.rectangle(orig_frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Track ID badge
                    badge = f"TRACK {t.track_id:02d} | {t.confidence:.2f}"
                    cv2.putText(
                        orig_frame,
                        badge,
                        (x1, max(y1 - 8, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        color,
                        2
                    )

                    # Draw motion trajectory trail
                    if t.history and len(t.history) > 1:
                        for p_idx in range(1, len(t.history)):
                            cv2.line(orig_frame, t.history[p_idx - 1], t.history[p_idx], color, 2)

                active_count = len(tracks)
                frame_to_show = orig_frame
            else:
                frame_to_show = np.zeros((display_h, display_w, 3), dtype=np.uint8)
                active_count = 0

            resized_frame = cv2.resize(frame_to_show, (display_w, display_h))

            metrics_payload = {
                "source_type": src_label,
                "resolution": f"{video_src.width()} x {video_src.height()}",
                "active_tracks": active_count,
                "total_seen": len(tracker.total_tracks_seen),
                "input_fps": metrics.input_fps,
                "tracking_fps": metrics.process_fps,
                "track_latency_ms": track_latency_ms,
                "queue_size": buffer.size(),
                "max_queue": buffer.max_size,
                "dropped": buffer.dropped_frames,
            }

            hud = build_tracking_hud(display_w, metrics_payload)
            canvas = np.vstack([resized_frame, hud])

            if not args.no_display:
                cv2.imshow("AI Attendance - Week 2 Multi-Object Tracking", canvas)
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
        print(f"Tracking pipeline stopped. Total frames: {consumed}")


if __name__ == "__main__":
    main()
