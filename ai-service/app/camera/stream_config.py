"""Stream Configuration and Camera State Models."""
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any
from enum import Enum

class CameraConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    STREAMING = "STREAMING"
    DEGRADED = "DEGRADED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"

@dataclass
class CameraStreamConfig:
    camera_id: str
    source_type: str             # "rtsp", "webcam", "file", "mock"
    rtsp_url: Optional[str] = None
    classroom_id: str = "CLASSROOM_203"
    direction: str = "IN"        # "IN" or "OUT"
    resolution: Tuple[int, int] = (1280, 720)
    target_fps: int = 25
    line_y: int = 360
    reconnect_delay_sec: float = 3.0
    max_reconnect_attempts: int = 10
    roi_polygon: Optional[list] = None

