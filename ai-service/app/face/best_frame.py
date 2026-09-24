"""Best-Frame Selector: Buffers multi-frame observations for each track,
evaluates quality metrics, and selects the optimal highest-fidelity face crop for biometric recognition.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque
import cv2
import numpy as np
import time

@dataclass
class FaceCandidate:
    crop: np.ndarray
    bbox: Tuple[int, int, int, int]
    confidence: float
    sharpness_score: float
    size_score: float
    lighting_score: float
    composite_score: float
    timestamp: float = field(default_factory=time.time)

class TrackCaptureBuffer:
    """Maintains a bounded ring buffer of candidate face frames for a single person track."""
    def __init__(self, max_candidates: int = 8):
        self.max_candidates = max_candidates
        self.candidates: deque = deque(maxlen=max_candidates)

    def add_candidate(
        self,
        crop: np.ndarray,
        bbox: Tuple[int, int, int, int],
        confidence: float = 0.90
    ) -> FaceCandidate:
        if crop is None or crop.size == 0:
            candidate = FaceCandidate(
                crop=crop, bbox=bbox, confidence=0.0,
                sharpness_score=0.0, size_score=0.0, lighting_score=0.0,
                composite_score=0.0
            )
            return candidate

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop

        # 1. Sharpness / Blur score
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness_var = float(lap.var())
        # Normalized between 0.0 and 1.0 (200.0+ is razor sharp)
        norm_sharpness = min(1.0, sharpness_var / 200.0)

        # 2. Size score (wider face = more biometric pixels)
        fw = bbox[2] - bbox[0]
        # Normalized between 0.0 and 1.0 (80px+ is high quality)
        norm_size = min(1.0, max(0.0, (fw - 20) / 60.0))

        # 3. Lighting score (penalize extreme dark or washed out faces)
        mean_lum = float(np.mean(gray))
        norm_lum = max(0.0, 1.0 - abs(mean_lum - 120.0) / 120.0)

        # 4. Composite Quality Score
        # Weights: 45% sharpness, 35% size, 20% lighting
        composite = (
            (0.45 * norm_sharpness)
            + (0.35 * norm_size)
            + (0.20 * norm_lum)
        ) * confidence

        candidate = FaceCandidate(
            crop=crop,
            bbox=bbox,
            confidence=confidence,
            sharpness_score=round(norm_sharpness, 3),
            size_score=round(norm_size, 3),
            lighting_score=round(norm_lum, 3),
            composite_score=round(composite, 3)
        )
        self.candidates.append(candidate)
        return candidate

    def get_best_candidate(self) -> Optional[FaceCandidate]:
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda c: c.composite_score)

    def size(self) -> int:
        return len(self.candidates)

class BestFrameSelector:
    """Campus-wide or camera-level manager for multi-track best frame selection."""
    def __init__(self, max_buffer_per_track: int = 8):
        self.max_buffer = max_buffer_per_track
        # track_id -> TrackCaptureBuffer
        self.track_buffers: Dict[int, TrackCaptureBuffer] = {}

    def add_track_observation(
        self,
        track_id: int,
        crop: np.ndarray,
        bbox: Tuple[int, int, int, int],
        confidence: float = 0.90
    ) -> FaceCandidate:
        if track_id not in self.track_buffers:
            self.track_buffers[track_id] = TrackCaptureBuffer(max_candidates=self.max_buffer)
        return self.track_buffers[track_id].add_candidate(crop, bbox, confidence)

    def select_best(self, track_id: int) -> Optional[FaceCandidate]:
        if track_id not in self.track_buffers:
            return None
        return self.track_buffers[track_id].get_best_candidate()

    def clear_track(self, track_id: int):
        if track_id in self.track_buffers:
            del self.track_buffers[track_id]
