"""Resilient RTSP Video Source Adapter with Auto-Reconnect and State Tracking."""
import cv2
import time
import threading
import numpy as np
from typing import Optional, Tuple

from app.camera.stream_config import CameraStreamConfig, CameraConnectionState
from app.camera.reconnect import ReconnectPolicy
from app.camera.health_monitor import default_health_monitor

class RTSPVideoSource:
    def __init__(self, config: CameraStreamConfig):
        self.config = config
        self.state = CameraConnectionState.DISCONNECTED
        self.cap: Optional[cv2.VideoCapture] = None
        self.reconnect_policy = ReconnectPolicy(
            base_delay_sec=config.reconnect_delay_sec,
            max_attempts=config.max_reconnect_attempts
        )
        self.reconnect_count = 0
        self.frames_read = 0
        self.fps_counter = 0
        self.last_fps_calc = time.perf_counter()
        self.measured_fps = 0.0

        self._connect()

    def _connect(self) -> bool:
        self.state = CameraConnectionState.CONNECTED
        url = self.config.rtsp_url or "0"

        try:
            # Check if using webcam or numeric device
            if url.isdigit():
                self.cap = cv2.VideoCapture(int(url))
            else:
                self.cap = cv2.VideoCapture(url)

            if self.cap and self.cap.isOpened():
                self.state = CameraConnectionState.STREAMING
                self.reconnect_policy.reset()
                return True
            else:
                self.state = CameraConnectionState.DEGRADED
                return False
        except Exception as e:
            self.state = CameraConnectionState.DISCONNECTED
            return False

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Reads a frame; handles network dropouts via non-blocking reconnect."""
        if self.cap is None or not self.cap.isOpened():
            if self.reconnect_policy.can_reconnect():
                self.reconnect_policy.record_attempt()
                self.reconnect_count += 1
                self.state = CameraConnectionState.RECONNECTING
                self._connect()
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.state = CameraConnectionState.DEGRADED
            if self.cap:
                self.cap.release()
                self.cap = None
            return False, None

        self.frames_read += 1
        self.fps_counter += 1
        now = time.perf_counter()
        if (now - self.last_fps_calc) >= 1.0:
            self.measured_fps = self.fps_counter / (now - self.last_fps_calc)
            self.fps_counter = 0
            self.last_fps_calc = now

            # Update central health monitor
            default_health_monitor.update_metrics(
                camera_id=self.config.camera_id,
                state=self.state,
                fps=self.measured_fps,
                dropped=0,
                queue_size=0,
                latency_ms=0.0,
                reconnects=self.reconnect_count
            )

        return True, frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.state = CameraConnectionState.DISCONNECTED

