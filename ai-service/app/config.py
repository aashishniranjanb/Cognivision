"""Central configuration for AI Service Video Ingestion."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / "configs" / ".env")

@dataclass
class CameraConfig:
    camera_id: str
    source: str
    location: str
    direction: str  # "IN" or "OUT"
    reconnect_interval_sec: float = 3.0
    buffer_size: int = 30

@dataclass
class AppConfig:
    cameras: list[CameraConfig]
    buffer_maxsize: int = int(os.getenv("FRAME_BUFFER_MAXSIZE", "30"))
    metrics_window_sec: float = float(os.getenv("METRICS_WINDOW_SEC", "3.0"))

def get_default_config() -> AppConfig:
    entry_src = os.getenv("ENTRY_CAMERA_URL", "mock")
    exit_src = os.getenv("EXIT_CAMERA_URL", "mock")
    
    # Try converting numeric strings to int (e.g. webcam "0")
    if entry_src.isdigit():
        entry_src = int(entry_src)
    if exit_src.isdigit():
        exit_src = int(exit_src)

    return AppConfig(
        cameras=[
            CameraConfig(
                camera_id="ENTRY_CAM_01",
                source=entry_src,
                location="CLASSROOM_203",
                direction="IN"
            ),
            CameraConfig(
                camera_id="EXIT_CAM_01",
                source=exit_src,
                location="CLASSROOM_203",
                direction="OUT"
            )
        ]
    )
