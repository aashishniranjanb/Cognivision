"""Week 1 Unified Main Demo: Supports Laptop Webcam & Recorded Video with Decoupled Buffer & HUD."""
import argparse
import sys
import os
import time
import threading
from pathlib import Path
import cv2
import numpy as np

# Ensure ai-service root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.camera.source import VideoSource
from app.pipeline.frame_queue import FrameBuffer, BufferedFrame
from app.metrics.ingestion_metrics import IngestionMetrics

def build_hud_panel(frame_w: int, metrics_data: dict) -> np.ndarray:
    """Builds a diagnostic HUD info panel rendered beneath the video frame."""
    hud_h = 160
    hud = np.zeros((hud_h, frame_w, 3), dtype=np.uint8)
    hud[:] = (20, 20, 24)

    # Header accent line
    cv2.line(hud, (0, 0), (frame_w, 0), (50, 200, 255), 2)
    cv2.putText(
        hud,
        "AI VIDEO ATTENDANCE — WEEK 1 INGESTION ENGINE",
        (20, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (50, 220, 255),
        2
    )

    col1_x = 25
    col2_x = max(frame_w // 2, 340)

    # Column 1: Source & Resolution
    cv2.putText(hud, f"SOURCE       : {metrics_data['source_type']}", (col1_x, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"RESOLUTION   : {metrics_data['resolution']}", (col1_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"STATUS       : {metrics_data['status']}", (col1_x, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 120), 2)

    # Column 2: Ingestion & Buffer Telemetry
    cv2.putText(hud, f"INPUT FPS    : {metrics_data['input_fps']:.1f}", (col2_x, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"PROCESS FPS  : {metrics_data['process_fps']:.1f}  (Latency: {metrics_data['latency_ms']:.1f}ms)", (col2_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1)
    cv2.putText(hud, f"QUEUE BUFFER : {metrics_data['queue_size']} / {metrics_data['max_queue']}  (Dropped: {metrics_data['dropped']})", (col2_x, 118), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 220, 255), 1)

    cv2.putText(hud, "Press 'q' or ESC to exit", (frame_w - 210, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (130, 130, 130), 1)
    return hud


def main():
    default_video = Path(__file__).resolve().parent.parent / "data" / "videos" / "test_video.mp4"

    parser = argparse.ArgumentParser(description="AI Video Attendance - Week 1 Ingestion Pipeline")
    parser.add_argument("--source", type=str, default="webcam", help="'webcam' (or 0) for laptop camera, or path to MP4 video")
    parser.add_argument("--max-queue", type=int, default=30, help="Frame buffer capacity")
    parser.add_argument("--no-display", action="store_true", help="Run without UI window for automated benchmarking")
    parser.add_argument("--max-frames", type=int, default=-1, help="Max frames to process before auto-exit")
    args = parser.parse_args()

    # Determine input source
    if args.source == "webcam" or args.source == "0":
        src_target = 0
        src_label = "LAPTOP WEBCAM"
    else:
        src_target = args.source if os.path.isabs(args.source) or os.path.exists(args.source) else str(default_video)
        src_label = f"VIDEO ({Path(src_target).name})"

    print("=" * 60)
    print("  AI VIDEO ATTENDANCE — WEEK 1 INGESTION ENGINE")
    print("=" * 60)
    print(f" Target Input : {src_label} [{src_target}]")
    print(f" Frame Buffer : Maxsize {args.max_queue} (Drop-oldest enabled)")
    print("=" * 60)

    try:
        video_src = VideoSource(src_target, loop=True)
    except Exception as e:
        print(f"[ERROR] Failed to initialize video source: {e}")
        return

    buffer = FrameBuffer(max_size=args.max_queue)
    metrics = IngestionMetrics(window_sec=3.0)
    running = True

    # Thread 1: Camera Ingestion Worker
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

            # Cap capture speed for video file so it replays at realistic pace
            if isinstance(src_target, str) and video_src.fps() > 0:
                time.sleep(1.0 / (video_src.fps() * 1.1))

    capture_thread = threading.Thread(target=capture_worker, name="CaptureThread", daemon=True)
    capture_thread.start()

    # Consumer / Display Loop
    consumed_frames = 0
    display_w, display_h = 960, 540

    try:
        while running:
            pkt = buffer.get(timeout=0.05)
            now = time.perf_counter()

            if pkt is not None:
                latency = (now - pkt.timestamp) * 1000.0
                metrics.record_processed(latency)
                consumed_frames += 1
                curr_frame = pkt.frame
            else:
                curr_frame = np.zeros((display_h, display_w, 3), dtype=np.uint8)

            resized_frame = cv2.resize(curr_frame, (display_w, display_h))

            # Render HUD
            metrics_payload = {
                "source_type": src_label,
                "resolution": f"{video_src.width()} x {video_src.height()}",
                "status": "ONLINE",
                "input_fps": metrics.input_fps,
                "process_fps": metrics.process_fps,
                "latency_ms": metrics.latency_ms,
                "queue_size": buffer.size(),
                "max_queue": buffer.max_size,
                "dropped": buffer.dropped_frames,
            }
            hud = build_hud_panel(display_w, metrics_payload)
            canvas = np.vstack([resized_frame, hud])

            if not args.no_display:
                cv2.imshow("AI Attendance - Week 1 Pipeline", canvas)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break

            if args.max_frames > 0 and consumed_frames >= args.max_frames:
                break

    finally:
        running = False
        capture_thread.join(timeout=1.0)
        video_src.release()
        if not args.no_display:
            cv2.destroyAllWindows()
        print(f"Pipeline stopped. Total processed frames: {consumed_frames}")


if __name__ == "__main__":
    main()
