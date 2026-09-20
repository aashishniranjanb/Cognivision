"""Generates a challenging multi-person CCTV test video featuring crossing paths and temporary occlusion."""
import cv2
import numpy as np
from pathlib import Path

def generate_multi_person_cctv(output_path: str = "ai-service/data/videos/multi_person_test.mp4", duration_sec: int = 12, fps: int = 30):
    w, h = 1280, 720
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(out_file), fourcc, fps, (w, h))

    total_frames = duration_sec * fps
    print(f"Generating {total_frames} frames multi-person crossing video: {out_file}...")

    # Simulated humans with realistic torso/head silhouettes to trigger YOLOv8n person detection
    def draw_person(canvas, cx, cy, color, scale=1.0):
        head_r = int(18 * scale)
        head_cy = cy - int(90 * scale)
        cv2.circle(canvas, (cx, head_cy), head_r, (210, 180, 140), -1)
        
        # Torso / jacket
        cv2.rectangle(canvas, (cx - int(25 * scale), head_cy + head_r), (cx + int(25 * scale), cy + int(40 * scale)), color, -1)
        # Legs
        cv2.rectangle(canvas, (cx - int(22 * scale), cy + int(40 * scale)), (cx - int(5 * scale), cy + int(120 * scale)), (30, 30, 80), -1)
        cv2.rectangle(canvas, (cx + int(5 * scale), cy + int(40 * scale)), (cx + int(22 * scale), cy + int(120 * scale)), (30, 30, 80), -1)

    for i in range(total_frames):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (50, 52, 55)  # Hallway corridor wall/floor

        # Perspective corridor
        cv2.rectangle(frame, (120, 120), (w - 120, h - 90), (68, 70, 75), -1)
        cv2.line(frame, (120, 120), (450, 260), (90, 95, 100), 2)
        cv2.line(frame, (w - 120, 120), (w - 450, 260), (90, 95, 100), 2)

        # Classroom Doorway
        cv2.rectangle(frame, (540, 220), (740, 520), (0, 140, 255), 3)
        cv2.putText(frame, "CLASSROOM 203 ENTRY", (520, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)

        # Static Pillar (for Occlusion test)
        pillar_x1, pillar_x2 = 620, 680
        cv2.rectangle(frame, (pillar_x1, 150), (pillar_x2, 600), (35, 38, 42), -1)
        cv2.putText(frame, "PILLAR", (pillar_x1, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        # Person 1: Walking LEFT to RIGHT (Entering)
        p1_x = int(160 + (i * 6.5) % (w - 320))
        p1_y = 380 + int(8 * np.sin(i * 0.2))
        draw_person(frame, p1_x, p1_y, (180, 50, 50), scale=1.1)

        # Person 2: Walking RIGHT to LEFT (Crossing Person 1)
        p2_x = int(w - 200 - (i * 5.8) % (w - 320))
        p2_y = 400 + int(8 * np.cos(i * 0.2))
        draw_person(frame, p2_x, p2_y, (40, 140, 60), scale=1.15)

        # Person 3: Walking down the corridor towards camera
        p3_scale = 0.7 + 0.5 * (i / total_frames)
        p3_x = 420 + int(20 * np.sin(i * 0.1))
        p3_y = int(280 + 160 * (i / total_frames))
        draw_person(frame, p3_x, p3_y, (50, 90, 180), scale=p3_scale)

        # Redraw Pillar in front of Person 1 when passing behind it (Temporary Occlusion)
        if pillar_x1 - 30 <= p1_x <= pillar_x2 + 30:
            cv2.rectangle(frame, (pillar_x1, 150), (pillar_x2, 600), (35, 38, 42), -1)

        cv2.putText(frame, f"MULTI-PERSON TEST | FRAME: {i}", (30, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        writer.write(frame)

    writer.release()
    print(f"Video saved: {out_file}")

if __name__ == "__main__":
    generate_multi_person_cctv()
