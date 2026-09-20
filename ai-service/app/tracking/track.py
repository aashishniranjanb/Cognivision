"""Track data structure representing a persistent person trajectory."""
from dataclasses import dataclass
from typing import Tuple, List, Optional
import time

@dataclass
class Track:
    track_id: int
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    timestamp: float
    hits: int = 1
    age: int = 1
    history: Optional[List[Tuple[int, int]]] = None  # centroid trajectory [(cx, cy), ...]

    @property
    def centroid(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return (int((x1 + x2) / 2), int((y1 + y2) / 2))
