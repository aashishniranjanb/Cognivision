"""Person Detection module filtered exclusively to class 'person'."""
import time
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from ultralytics import YOLO

@dataclass
class Detection:
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    class_name: str

class PersonDetector:
    def __init__(self, model_name: str = "yolov8n.pt", conf_thresh: float = 0.45, device: str = "cpu"):
        self.conf_thresh = conf_thresh
        self.device = device
        print(f"[PersonDetector] Loading {model_name} on device '{device}'...")
        self.model = YOLO(model_name)
        # Warmup
        dummy = np.zeros((384, 640, 3), dtype=np.uint8)
        self.model.predict(dummy, classes=[0], verbose=False, device=self.device)
        print("[PersonDetector] Model loaded and warmed up.")

    def detect(self, frame: np.ndarray) -> Tuple[List[Detection], float]:
        """Detects people in a single frame. Returns detections and inference time in ms."""
        start = time.perf_counter()
        
        # classes=[0] filters exclusively for COCO class 'person'
        results = self.model.predict(
            source=frame,
            classes=[0],
            conf=self.conf_thresh,
            device=self.device,
            verbose=False,
            imgsz=640
        )
        latency_ms = (time.perf_counter() - start) * 1000.0

        detections = []
        if results and len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0].cpu().numpy())
                detections.append(Detection(
                    bbox=(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])),
                    confidence=conf,
                    class_id=0,
                    class_name="person"
                ))

        return detections, latency_ms
