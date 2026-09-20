"""CLI Entry point for Week 1 Stream Ingestion & HUD Monitoring."""
import argparse
import sys
import os

# Add ai-service to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_default_config, CameraConfig
from app.camera.camera_manager import CameraManager
from app.pipeline import Week1Pipeline

def main():
    parser = argparse.ArgumentParser(description="AI Attendance System - Week 1 Stream Ingestion Demo")
    parser.add_argument("--source", type=str, default=None, help="Camera source (0 for webcam, 'mock' for synthetic, or RTSP URL)")
    parser.add_argument("--no-display", action="store_true", help="Run headless without cv2.imshow")
    parser.add_argument("--frames", type=int, default=-1, help="Max frames to run (-1 for infinite)")
    args = parser.parse_args()

    cfg = get_default_config()

    if args.source:
        src = int(args.source) if args.source.isdigit() else args.source
        cfg.cameras = [
            CameraConfig(
                camera_id="CAM_TEST_01",
                source=src,
                location="CLASSROOM_203",
                direction="IN"
            )
        ]

    print("==========================================================")
    print("  AI VIDEO ATTENDANCE SYSTEM — WEEK 1 INGESTION ENGINE   ")
    print("==========================================================")
    for cam in cfg.cameras:
        print(f" -> Camera: {cam.camera_id} | Location: {cam.location} | Source: {cam.source}")
    print("==========================================================")
    print(" Press 'q' or 'ESC' on the live display window to quit.")
    print("==========================================================")

    manager = CameraManager(cfg.cameras)
    pipeline = Week1Pipeline(manager)

    try:
        pipeline.run_live(display=not args.no_display, max_frames=args.frames)
    except KeyboardInterrupt:
        print("\nStopping ingestion pipeline...")
    finally:
        pipeline.stop()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
