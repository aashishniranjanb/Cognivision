"""Common Modality Observation contract for Multimodal Biometric Fusion."""
from dataclasses import dataclass, asdict
from typing import Optional
import json

@dataclass
class ModalityObservation:
    modality: str                  # "face", "body", "gait"
    candidate_id: Optional[str]    # e.g., "STU001" or None
    identity_score: float          # Match similarity [0.0, 1.0]
    reliability: float             # Measured observation quality/trustworthiness [0.0, 1.0]
    track_id: int
    timestamp: float

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
