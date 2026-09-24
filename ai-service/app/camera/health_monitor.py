"""Camera Health Telemetry Monitor: Tracks FPS, Latency, Dropped Frames, and Connection State."""
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from app.camera.stream_config import CameraConnectionState

@dataclass
class CameraHealthMetrics:
    camera_id: str
    state: CameraConnectionState
    measured_fps: float
    dropped_frames: int
    queue_depth: int
    pipeline_latency_ms: float
    last_frame_timestamp: float
    reconnect_count: int
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["state"] = self.state.value if isinstance(self.state, CameraConnectionState) else str(self.state)
        return d

class CameraHealthMonitor:
    def __init__(self):
        self.health_records: Dict[str, CameraHealthMetrics] = {}

    def update_metrics(
        self,
        camera_id: str,
        state: CameraConnectionState,
        fps: float,
        dropped: int,
        queue_size: int,
        latency_ms: float,
        reconnects: int,
        error: Optional[str] = None
    ) -> CameraHealthMetrics:
        rec = CameraHealthMetrics(
            camera_id=camera_id,
            state=state,
            measured_fps=round(fps, 1),
            dropped_frames=dropped,
            queue_depth=queue_size,
            pipeline_latency_ms=round(latency_ms, 2),
            last_frame_timestamp=time.time(),
            reconnect_count=reconnects,
            error_message=error
        )
        self.health_records[camera_id] = rec
        return rec

    def get_health(self, camera_id: str) -> Optional[CameraHealthMetrics]:
        return self.health_records.get(camera_id)

    def get_all_health(self) -> Dict[str, dict]:
        return {cid: rec.to_dict() for cid, rec in self.health_records.items()}

    def record_failure(self, camera_id: str, error: str = "RTSP stream lost") -> CameraHealthMetrics:
        return self.update_metrics(
            camera_id=camera_id,
            state=CameraConnectionState.DISCONNECTED,
            fps=0.0,
            dropped=10,
            queue_size=0,
            latency_ms=999.0,
            reconnects=1,
            error=error
        )

    def record_frame(self, camera_id: str, fps: float = 25.0) -> CameraHealthMetrics:
        return self.update_metrics(
            camera_id=camera_id,
            state=CameraConnectionState.STREAMING,
            fps=fps,
            dropped=0,
            queue_size=1,
            latency_ms=40.0,
            reconnects=0,
            error=None
        )

# Global health monitor singleton
default_health_monitor = CameraHealthMonitor()

