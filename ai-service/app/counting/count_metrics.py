"""Counting & Capture Quality Metrics for SRM Phase-I & Phase-II Evaluation."""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class CampusKPISummary:
    expected_students: int
    physical_detected: int
    active_tracks: int
    successfully_identified: int
    unknown_count: int
    uncertain_count: int
    current_occupancy: int
    
    # KPIs
    capture_success_rate: float       # detected / expected
    tracking_success_rate: float      # active_tracks / detected
    identity_success_rate: float      # identified / active_tracks
    overall_pipeline_success: float   # identified / expected

def compute_campus_kpis(
    expected_students: int,
    physical_detected: int,
    active_tracks: int,
    successfully_identified: int,
    unknown_count: int,
    uncertain_count: int,
    current_occupancy: int
) -> CampusKPISummary:
    exp = max(1, expected_students)
    det = max(1, physical_detected)
    trk = max(1, active_tracks)

    capture_rate = min(1.0, physical_detected / exp)
    tracking_rate = min(1.0, active_tracks / det)
    identity_rate = min(1.0, successfully_identified / trk)
    overall = min(1.0, successfully_identified / exp)

    return CampusKPISummary(
        expected_students=expected_students,
        physical_detected=physical_detected,
        active_tracks=active_tracks,
        successfully_identified=successfully_identified,
        unknown_count=unknown_count,
        uncertain_count=uncertain_count,
        current_occupancy=current_occupancy,
        capture_success_rate=round(capture_rate, 4),
        tracking_success_rate=round(tracking_rate, 4),
        identity_success_rate=round(identity_rate, 4),
        overall_pipeline_success=round(overall, 4)
    )
