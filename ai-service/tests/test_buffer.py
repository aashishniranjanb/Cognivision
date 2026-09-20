"""Tests for decoupled frame buffer queue mechanics and drop policy."""
import time
import numpy as np
import pytest
from app.buffer.frame_buffer import FrameBuffer, FramePacket

def test_frame_buffer_push_and_pop():
    buf = FrameBuffer(maxsize=5)
    dummy_frame = np.zeros((10, 10, 3), dtype=np.uint8)

    packet = FramePacket(frame_id=1, camera_id="CAM_01", timestamp=time.time(), frame=dummy_frame)
    dropped = buf.push(packet)
    assert not dropped
    assert buf.qsize == 1

    popped = buf.pop(timeout=0.1)
    assert popped is not None
    assert popped.frame_id == 1
    assert buf.qsize == 0

def test_frame_buffer_drop_oldest_overflow():
    buf = FrameBuffer(maxsize=3)
    dummy = np.zeros((10, 10, 3), dtype=np.uint8)

    # Push 3 items
    for i in range(1, 4):
        buf.push(FramePacket(frame_id=i, camera_id="CAM_01", timestamp=time.time(), frame=dummy))
    assert buf.qsize == 3
    assert buf.total_dropped == 0

    # Push 4th item (should drop item 1)
    dropped = buf.push(FramePacket(frame_id=4, camera_id="CAM_01", timestamp=time.time(), frame=dummy))
    assert dropped is True
    assert buf.qsize == 3
    assert buf.total_dropped == 1

    # First popped item should now be frame_id 2 (frame_id 1 was discarded)
    first_out = buf.pop(timeout=0.1)
    assert first_out.frame_id == 2
