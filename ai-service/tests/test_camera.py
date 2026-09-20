"""Tests for StreamReader and CameraManager."""
import time
from app.config import CameraConfig
from app.camera.camera_manager import CameraManager

def test_camera_manager_mock_ingestion():
    configs = [
        CameraConfig(camera_id="TEST_ENTRY", source="mock", location="ROOM_101", direction="IN", buffer_size=10),
        CameraConfig(camera_id="TEST_EXIT", source="mock", location="ROOM_101", direction="OUT", buffer_size=10)
    ]
    mgr = CameraManager(configs)
    mgr.start_all()

    # Allow mock threads to generate a few frames
    time.sleep(0.5)

    status = mgr.get_status_summary()
    assert "TEST_ENTRY" in status
    assert "TEST_EXIT" in status
    assert status["TEST_ENTRY"]["connected"] is True
    assert status["TEST_EXIT"]["connected"] is True
    assert status["TEST_ENTRY"]["queue_size"] > 0

    mgr.stop_all()
