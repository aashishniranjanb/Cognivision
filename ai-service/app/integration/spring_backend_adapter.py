"""Spring Boot Backend Integration Adapter.
Dispatches confirmed AI identity events to attendance-backend (REST API on port 8080).
"""
import logging
import urllib.request
import urllib.error
import json
from datetime import datetime
from typing import Optional

from app.events.event_schema import CampusEvent

logger = logging.getLogger("SpringBackendAdapter")

class SpringBackendAdapter:
    def __init__(self, backend_url: str = "http://localhost:8080/api"):
        self.backend_url = backend_url.rstrip("/")
        self.identity_endpoint = f"{self.backend_url}/events/identity"

    def forward_event(self, event: CampusEvent) -> bool:
        """Translates CampusEvent into IdentityEventRequest and dispatches to Spring Boot backend."""
        # Only forward events with an identified student
        if not event.student_id or event.student_id in ["UNKNOWN", "None"]:
            return False

        # Map camera to registered camera ID in backend
        cam_id = event.camera_id
        if "EXIT" in cam_id:
            mapped_cam = "CAM02"
        else:
            mapped_cam = "CAM01"

        direction = event.event_type if event.event_type in ["IN", "OUT"] else "IN"
        conf = float(event.confidence) if event.confidence is not None else 0.90
        event_type = "IDENTITY_CONFIRMED" if conf >= 0.70 else "PROVISIONAL"

        ts_str = event.timestamp_iso
        if not ts_str:
            ts_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        payload = {
            "trackId": str(event.track_id),
            "candidateId": event.student_id,
            "cameraId": mapped_cam,
            "eventType": event_type,
            "confidence": conf,
            "direction": direction,
            "timestamp": ts_str
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.identity_endpoint,
                data=data,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status in [200, 201]:
                    logger.info(f"Successfully forwarded event for {event.student_id} ({direction}) to backend")
                    return True
                else:
                    logger.warning(f"Backend responded with status {response.status}")
                    return False
        except urllib.error.URLError as e:
            # Backend may not be started yet or offline
            logger.debug(f"Could not reach backend at {self.identity_endpoint}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error forwarding event to backend: {e}")
            return False

# Global singleton instance
default_spring_adapter = SpringBackendAdapter()
