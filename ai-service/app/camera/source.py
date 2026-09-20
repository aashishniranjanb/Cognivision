"""Unified Video Source abstraction for Webcam, Recorded MP4/AVI, and future RTSP feeds."""
import cv2
from typing import Union, Tuple, Optional


class VideoSource:
    def __init__(self, source: Union[int, str], loop: bool = True):
        self.source = source
        self.loop = loop
        self.cap = cv2.VideoCapture(source)

        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open video source: {source}")

        # Cache properties
        self._fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def read(self) -> Tuple[bool, Optional[any]]:
        ret, frame = self.cap.read()
        if not ret and self.loop and isinstance(self.source, str):
            # Rewind prerecorded video automatically
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
        return ret, frame

    def fps(self) -> float:
        return self._fps

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height

    def is_opened(self) -> bool:
        return self.cap.isOpened()

    def release(self):
        if self.cap:
            self.cap.release()
