"""Person Counting Engine: Tracks individual track IDs, filters false positive noise via temporal confirmation,
and provides true physical person counts decoupled from identity recognition.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional, Tuple
import time

class TrackState(str, Enum):
    NEW = "NEW"
    TENTATIVE = "TENTATIVE"
    CONFIRMED = "CONFIRMED"
    LOST = "LOST"

@dataclass
class TrackHistory:
    track_id: int
    state: TrackState = TrackState.NEW
    hit_count: int = 1
    lost_count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    has_entered: bool = False
    has_exited: bool = False

class PersonCounter:
    """Manages physical person counting on a per-camera or per-zone basis.
    Enforces that physical people are confirmed by persistent track continuity
    rather than single-frame detections or shadows.
    """
    def __init__(self, min_confirm_frames: int = 3, max_lost_frames: int = 10):
        self.min_confirm_frames = min_confirm_frames
        self.max_lost_frames = max_lost_frames
        
        # track_id -> TrackHistory
        self.tracks: Dict[int, TrackHistory] = {}
        
        # Cumulative unique person crossings
        self.entered_track_ids: Set[int] = set()
        self.exited_track_ids: Set[int] = set()

    def update(self, detected_track_ids: List[int], timestamp: Optional[float] = None) -> Dict[str, int]:
        """Updates internal track continuity states with current frame track IDs.
        Returns immediate physical counts for the frame.
        """
        now = timestamp if timestamp is not None else time.time()
        detected_set = set(detected_track_ids)

        # 1. Update matched tracks
        for tid in detected_set:
            if tid in self.tracks:
                rec = self.tracks[tid]
                rec.hit_count += 1
                rec.lost_count = 0
                rec.last_seen = now
                if rec.hit_count >= self.min_confirm_frames:
                    rec.state = TrackState.CONFIRMED
                else:
                    rec.state = TrackState.TENTATIVE
            else:
                self.tracks[tid] = TrackHistory(
                    track_id=tid,
                    state=TrackState.TENTATIVE if self.min_confirm_frames > 1 else TrackState.CONFIRMED,
                    hit_count=1,
                    first_seen=now,
                    last_seen=now
                )

        # 2. Update missing tracks
        to_delete = []
        for tid, rec in self.tracks.items():
            if tid not in detected_set:
                rec.lost_count += 1
                if rec.lost_count > self.max_lost_frames:
                    rec.state = TrackState.LOST
                    to_delete.append(tid)

        for tid in to_delete:
            del self.tracks[tid]

        return self.get_summary()

    def record_crossing(self, track_id: int, direction: str) -> bool:
        """Records a directional crossing (IN/OUT) for a confirmed track."""
        if track_id not in self.tracks:
            # Register ad-hoc if not present
            self.tracks[track_id] = TrackHistory(track_id=track_id, state=TrackState.CONFIRMED)

        rec = self.tracks[track_id]
        if direction.upper() == "IN":
            rec.has_entered = True
            self.entered_track_ids.add(track_id)
            return True
        elif direction.upper() == "OUT":
            rec.has_exited = True
            self.exited_track_ids.add(track_id)
            return True
        return False

    @property
    def current_physical_count(self) -> int:
        """Physical people currently visible in frame with confirmed tracks."""
        return sum(1 for rec in self.tracks.values() if rec.state == TrackState.CONFIRMED and rec.lost_count == 0)

    @property
    def active_track_count(self) -> int:
        """Total active tracks including tentative and recently coasted."""
        return len(self.tracks)

    @property
    def confirmed_track_ids(self) -> List[int]:
        return [tid for tid, rec in self.tracks.items() if rec.state == TrackState.CONFIRMED and rec.lost_count == 0]

    @property
    def tentative_track_ids(self) -> List[int]:
        return [tid for tid, rec in self.tracks.items() if rec.state == TrackState.TENTATIVE]

    def get_summary(self) -> dict:
        return {
            "physical_count": self.current_physical_count,
            "active_tracks": self.active_track_count,
            "confirmed_tracks": len(self.confirmed_track_ids),
            "tentative_tracks": len(self.tentative_track_ids),
            "total_entered": len(self.entered_track_ids),
            "total_exited": len(self.exited_track_ids),
            "net_occupancy_change": len(self.entered_track_ids) - len(self.exited_track_ids)
        }
