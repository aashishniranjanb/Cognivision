"""Capture Zone & Funnel Manager defining high-confidence observation zones and crossing boundary lines."""
from typing import List, Tuple, Optional
import cv2
import numpy as np

class CaptureZone:
    def __init__(
        self,
        zone_polygon: Optional[List[Tuple[int, int]]] = None,
        crossing_line: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    ):
        # Default funnel capture zone if none provided
        self.polygon = zone_polygon or [(200, 100), (800, 100), (800, 500), (200, 500)]
        self.crossing_line = crossing_line or ((200, 300), (800, 300))
        self._poly_np = np.array(self.polygon, dtype=np.int32)

    def is_point_in_zone(self, pt: Tuple[int, int]) -> bool:
        """Determines if a 2D coordinate is physically inside the capture funnel."""
        return cv2.pointPolygonTest(self._poly_np, (float(pt[0]), float(pt[1])), False) >= 0

    def is_bbox_in_zone(self, bbox: Tuple[int, int, int, int]) -> bool:
        """Evaluates whether the center or base of a person bounding box is in the capture zone."""
        x1, y1, x2, y2 = bbox
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        base_y = int(y2)
        # Person counts as inside capture zone if either center or foot base is within the polygon
        return self.is_point_in_zone((center_x, center_y)) or self.is_point_in_zone((center_x, base_y))

    def evaluate_crossing(self, prev_y: float, curr_y: float) -> Optional[str]:
        """Simple, robust horizontal boundary line crossing evaluator.
        Assumes moving downward (increasing Y) is IN, moving upward is OUT.
        """
        line_y = float(self.crossing_line[0][1])
        if prev_y < line_y <= curr_y:
            return "IN"
        elif prev_y > line_y >= curr_y:
            return "OUT"
        return None
