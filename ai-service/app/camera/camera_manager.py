"""Multi-Camera Manager coordinating multiple stream readers, buffers, and metrics."""
import logging
from typing import Dict, Optional
from app.config import CameraConfig
from app.buffer.frame_buffer import FrameBuffer
from app.metrics.tracker import StreamMetrics
from app.camera.stream_reader import StreamReader

logger = logging.getLogger(__name__)

class CameraManager:
    def __init__(self, camera_configs: list[CameraConfig]):
        self.configs = camera_configs
        self.readers: Dict[str, StreamReader] = {}
        self.buffers: Dict[str, FrameBuffer] = {}
        self.metrics: Dict[str, StreamMetrics] = {}

        self._initialize()

    def _initialize(self):
        for cfg in self.configs:
            buf = FrameBuffer(maxsize=cfg.buffer_size)
            met = StreamMetrics()
            reader = StreamReader(
                camera_id=cfg.camera_id,
                source=cfg.source,
                buffer=buf,
                metrics=met,
                location=cfg.location,
                direction=cfg.direction,
                reconnect_delay_sec=cfg.reconnect_interval_sec
            )
            self.buffers[cfg.camera_id] = buf
            self.metrics[cfg.camera_id] = met
            self.readers[cfg.camera_id] = reader

    def start_all(self):
        logger.info(f"Starting {len(self.readers)} camera stream(s)...")
        for cam_id, reader in self.readers.items():
            reader.start()

    def stop_all(self):
        logger.info("Stopping all camera streams...")
        for cam_id, reader in self.readers.items():
            reader.stop()

    def get_status_summary(self) -> dict:
        summary = {}
        for cam_id, reader in self.readers.items():
            buf_stats = self.buffers[cam_id].stats()
            metrics = self.metrics[cam_id]
            summary[cam_id] = {
                "connected": reader.is_connected,
                "reconnect_attempts": reader.reconnect_attempts,
                "resolution": reader.resolution,
                "input_fps": metrics.input_fps,
                "processing_fps": metrics.processing_fps,
                "latency_ms": metrics.avg_latency_ms,
                "queue_size": buf_stats["size"],
                "queue_max": buf_stats["maxsize"],
                "dropped_frames": buf_stats["dropped"],
                "location": reader.location,
                "direction": reader.direction,
            }
        return summary
