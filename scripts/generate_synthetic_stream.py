"""Generates a realistic mock campus hallway / entry video file for offline CCTV testing."""
import cv2
import numpy as np
import time
from pathlib import Path

def generate_sample_clip(output_path: str, duration_sec: int = 10, fps: int = 30):
    w, h = 1280, 720
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(out_file), fourcc, fps, (w, h))

    total_frames = duration_sec * fps
    print(f"Generating {total_frames} frames ({duration_sec}s @ {fps}fps) to {out_file}...")

    for frame_idx in range(total_frames):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (45, 45, 48)  # Hallway background

        # Hallway perspective lines
        cv2.rectangle(frame, (100, 100), (w - 100, h - 80), (60, 60, 65), -1)
        cv2.line(frame, (100, 100), (400, 250), (90, 90, 95), 2)
        cv2.line(frame, (w - 100, 100), (w - 400, 250), (90, 90, 95), 2)

        # Classroom Doorway
        cv2.rectangle(frame, (500, 220), (780, 560), (0, 140, 255), 3)
        cv2.putText(frame, "CLASSROOM 203 ENTRYWAY", (510, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)

        # Simulated walking student (Target 1)
        cycle = (frame_idx * 6) % (w - 300)
        box_x = 150 + cycle
        box_y = 310 + int(20 * np.sin(frame_idx * 0.15))
        cv2.rectangle(frame, (box_x, box_y), (box_x + 90, box_y + 190), (0, 255, 120), 2)
        cv2.putText(frame, "PERSON #1", (box_x, box_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 1)

        # Timestamp watermark
        cv2.putText(frame, f"CCTV RECORDING - FRAME {frame_idx} - {fps} FPS", (30, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        writer.write(frame)

    writer.release()
    print(f"Sample clip created successfully: {out_file} ({out_file.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    generate_sample_clip("data/samples/sample_hallway.mp4", duration_sec=10)
