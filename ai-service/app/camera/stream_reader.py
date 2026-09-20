"""Threaded Video Stream Reader supporting RTSP, Webcam, Video Files, and Synthetic Mock."""
import time
import threading
import logging
from typing import Optional, Union
import cv2
import numpy as np

from app.buffer.frame_buffer import FrameBuffer, FramePacket
from app.metrics.tracker import StreamMetrics

logger = logging.getLogger(__name__)

class StreamReader:
    def __init__(
        self,
        camera_id: str,
        source: Union[int, str],
        buffer: FrameBuffer,
        metrics: StreamMetrics,
        location: str = "CLASSROOM_203",
        direction: str = "IN",
        reconnect_delay_sec: float = 3.0,
    ):
        self.camera_id = camera_id
        self.source = source
        self.buffer = buffer
        self.metrics = metrics
        self.location = location
        self.direction = direction
        self.reconnect_delay_sec = reconnect_delay_sec

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None
        
        # State
        self.is_connected = False
        self.reconnect_attempts = 0
        self.resolution = (0, 0)
        self.frame_counter = 0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, name=f"Reader-{self.camera_id}", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._release_capture()

    def _open_capture(self) -> bool:
        self._release_capture()
        if self.source == "mock":
            self.is_connected = True
            self.resolution = (1280, 720)
            return True

        logger.info(f"[{self.camera_id}] Connecting to source: {self.source}...")
        self._cap = cv2.VideoCapture(self.source)
        if self._cap and self._cap.isOpened():
            self.is_connected = True
            self.reconnect_attempts = 0
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.resolution = (w, h)
            logger.info(f"[{self.camera_id}] Connected. Resolution: {w}x{h}")
            return True
        else:
            self.is_connected = False
            return False

    def _release_capture(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self.is_connected = False

    def _generate_mock_frame(self) -> np.ndarray:
        """Generates a dynamic CCTV simulation frame (corridor/entryway pattern with moving target)."""
        w, h = 1280, 720
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        # Background floor and walls
        frame[:] = (45, 45, 48)
        cv2.rectangle(frame, (100, 100), (w - 100, h - 80), (60, 60, 65), -1)
        cv2.line(frame, (100, 100), (400, 250), (90, 90, 95), 2)
        cv2.line(frame, (w - 100, 100), (w - 400, 250), (90, 90, 95), 2)

        # Draw simulated door / zone
        door_color = (0, 140, 255) if self.direction == "IN" else (255, 140, 0)
        cv2.rectangle(frame, (500, 220), (780, 560), door_color, 3)
        cv2.putText(
            frame,
            f"ZONE: {self.location} [{self.direction}]",
            (510, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            door_color,
            2
        )

        # Moving person simulation box
        cycle = (self.frame_counter * 5) % (w - 300)
        box_x = 150 + cycle
        box_y = 300 + int(30 * np.sin(self.frame_counter * 0.1))
        cv2.rectangle(frame, (box_x, box_y), (box_x + 90, box_y + 190), (0, 255, 120), 2)
        cv2.putText(
            frame,
            "TEST_TARGET",
            (box_x, box_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 120),
            1
        )

        # Timestamp watermark
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame,
            f"CCTV SIMULATION - {self.camera_id} - {ts_str}",
            (30, h - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1
        )
        return frame

    def _capture_loop(self):
        while self._running:
            if not self.is_connected:
                success = self._open_capture()
                if not success:
                    self.reconnect_attempts += 1
                    time.sleep(self.reconnect_delay_sec)
                    continue

            if self.source == "mock":
                frame = self._generate_mock_frame()
                ret = True
                time.sleep(1.0 / 30.0)  # Simulate 30 FPS input
            else:
                ret, frame = self._cap.read()

            if not ret or frame is None:
                logger.warning(f"[{self.camera_id}] Frame read failed. Entering reconnect...")
                self.is_connected = False
                self.reconnect_attempts += 1
                time.sleep(self.reconnect_delay_sec)
                continue

            self.frame_counter += 1
            now = time.time()
            self.metrics.record_input_frame()

            packet = FramePacket(
                frame_id=self.frame_counter,
                camera_id=self.camera_id,
                timestamp=now,
                frame=frame,
                metadata={
                    "location": self.location,
                    "direction": self.direction,
                    "resolution": self.resolution
                }
            )

            self.buffer.push(packet)
