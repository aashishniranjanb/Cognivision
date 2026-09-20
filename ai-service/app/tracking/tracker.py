"""Multi-Object Tracker leveraging ByteTrack for persistent Person Track IDs."""
import time
from typing import List, Tuple, Dict
import numpy as np
from ultralytics import YOLO

from app.tracking.track import Track

class ByteTrackTracker:
    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        conf_thresh: float = 0.40,
        tracker_config: str = "bytetrack.yaml",
        device: str = "cpu"
    ):
        self.conf_thresh = conf_thresh
        self.tracker_config = tracker_config
        self.device = device
        
        print(f"[ByteTrackTracker] Initializing {model_name} with {tracker_config} on {device}...")
        self.model = YOLO(model_name)
        self.trajectory_history: Dict[int, List[Tuple[int, int]]] = {}
        self.total_tracks_seen: set[int] = set()

    def update(self, frame: np.ndarray) -> Tuple[List[Track], float]:
        """Runs detection + ByteTrack association on the frame. Returns persistent tracks and latency."""
        start = time.perf_counter()
        
        results = self.model.track(
            source=frame,
            classes=[0],             # COCO class 'person' exclusively
            conf=self.conf_thresh,
            tracker=self.tracker_config,
            persist=True,            # Maintains tracking state across sequential frames
            device=self.device,
            verbose=False,
            imgsz=640
        )
        latency_ms = (time.perf_counter() - start) * 1000.0

        tracks: List[Track] = []
        now = time.perf_counter()

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                if box.id is None:
                    continue  # Unassigned tentative detection

                track_id = int(box.id[0].cpu().numpy())
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0].cpu().numpy())

                self.total_tracks_seen.add(track_id)
                centroid = (int((xyxy[0] + xyxy[2]) / 2), int((xyxy[1] + xyxy[3]) / 2))

                if track_id not in self.trajectory_history:
                    self.trajectory_history[track_id] = []
                self.trajectory_history[track_id].append(centroid)
                if len(self.trajectory_history[track_id]) > 30:
                    self.trajectory_history[track_id].pop(0)

                tracks.append(Track(
                    track_id=track_id,
                    bbox=(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])),
                    confidence=conf,
                    class_id=0,
                    timestamp=now,
                    history=list(self.trajectory_history[track_id])
                ))

        return tracks, latency_ms

    def reset(self):
        self.trajectory_history.clear()
        self.total_tracks_seen.clear()
