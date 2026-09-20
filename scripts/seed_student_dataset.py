"""Generates synthetic student face datasets for STU001 to STU005 with pose & illumination variations."""
import cv2
import numpy as np
from pathlib import Path

def draw_synthetic_face(name: str, skin_tone, eye_color, hair_color, pose_dx=0, brightness_offset=0):
    w, h = 240, 240
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:] = (230, 230, 235)  # Clean backdrop

    cx, cy = 120 + pose_dx, 120

    # Neck
    cv2.rectangle(img, (cx - 25, cy + 45), (cx + 25, cy + 100), tuple(int(c * 0.9) for c in skin_tone), -1)

    # Head (ellipse)
    cv2.ellipse(img, (cx, cy), (55, 75), 0, 0, 360, skin_tone, -1)

    # Hair
    cv2.ellipse(img, (cx, cy - 35), (60, 45), 0, 180, 360, hair_color, -1)

    # Eyes
    eye_y = cy - 8
    cv2.circle(img, (cx - 22, eye_y), 7, (255, 255, 255), -1)
    cv2.circle(img, (cx + 22, eye_y), 7, (255, 255, 255), -1)
    cv2.circle(img, (cx - 22 + int(pose_dx*0.2), eye_y), 4, eye_color, -1)
    cv2.circle(img, (cx + 22 + int(pose_dx*0.2), eye_y), 4, eye_color, -1)

    # Eyebrows
    cv2.line(img, (cx - 32, eye_y - 12), (cx - 12, eye_y - 12), hair_color, 2)
    cv2.line(img, (cx + 12, eye_y - 12), (cx + 32, eye_y - 12), hair_color, 2)

    # Nose
    cv2.line(img, (cx, cy - 5), (cx - 3, cy + 16), (160, 130, 110), 2)
    cv2.line(img, (cx - 3, cy + 16), (cx + 4, cy + 16), (160, 130, 110), 2)

    # Mouth
    cv2.ellipse(img, (cx, cy + 34), (18, 8), 0, 0, 180, (120, 80, 80), 2)

    # Adjust illumination
    if brightness_offset != 0:
        img = np.clip(img.astype(np.int16) + brightness_offset, 0, 255).astype(np.uint8)

    # Add Gaussian blur / texture to simulate natural camera sensor
    img = cv2.GaussianBlur(img, (3, 3), 0.5)
    return img

def seed_sample_students():
    students = [
        {"id": "STU001", "name": "Aashish Kumar", "skin": (180, 150, 120), "eye": (40, 30, 20), "hair": (20, 20, 20)},
        {"id": "STU002", "name": "Priya Sharma", "skin": (195, 165, 135), "eye": (30, 50, 80), "hair": (30, 15, 10)},
        {"id": "STU003", "name": "Rahul Verma", "skin": (175, 140, 115), "eye": (50, 40, 30), "hair": (15, 15, 15)},
        {"id": "STU004", "name": "Sneha Patel", "skin": (200, 175, 145), "eye": (30, 30, 30), "hair": (40, 25, 20)},
        {"id": "STU005", "name": "Vikram Singh", "skin": (165, 135, 105), "eye": (25, 25, 25), "hair": (10, 10, 10)},
    ]

    base_dir = Path("data/students")
    base_dir.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic enrollment images for initial 5 students...")
    created_map = {}

    for s in students:
        sid = s["id"]
        sdir = base_dir / sid / "raw_captures"
        sdir.mkdir(parents=True, exist_ok=True)
        img_list = []

        # 1. Frontal neutral
        f1 = draw_synthetic_face(s["name"], s["skin"], s["eye"], s["hair"], pose_dx=0, brightness_offset=0)
        p1 = sdir / "pose_01_frontal.jpg"
        cv2.imwrite(str(p1), f1)
        img_list.append(str(p1))

        # 2. Slight left
        f2 = draw_synthetic_face(s["name"], s["skin"], s["eye"], s["hair"], pose_dx=-10, brightness_offset=5)
        p2 = sdir / "pose_02_left.jpg"
        cv2.imwrite(str(p2), f2)
        img_list.append(str(p2))

        # 3. Slight right
        f3 = draw_synthetic_face(s["name"], s["skin"], s["eye"], s["hair"], pose_dx=10, brightness_offset=-5)
        p3 = sdir / "pose_03_right.jpg"
        cv2.imwrite(str(p3), f3)
        img_list.append(str(p3))

        # 4. Mild lighting variation
        f4 = draw_synthetic_face(s["name"], s["skin"], s["eye"], s["hair"], pose_dx=0, brightness_offset=20)
        p4 = sdir / "pose_04_lighting.jpg"
        cv2.imwrite(str(p4), f4)
        img_list.append(str(p4))

        created_map[sid] = (s["name"], img_list)

    return created_map

if __name__ == "__main__":
    seed_sample_students()
