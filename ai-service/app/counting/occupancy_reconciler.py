"""Occupancy Reconciler: Compares physical vision headcount, event-derived occupancy,
and identified student presence to detect anomalies, quantify error localization, and explain discrepancies.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ReconciledOccupancyReport:
    classroom_id: str
    vision_count: int
    event_occupancy: int
    identified_count: int
    unknown_count: int
    uncertain_count: int
    difference: int
    status: str             # "PERFECT_MATCH", "MINOR_MISMATCH", "OCCUPANCY_MISMATCH"
    unidentified_present: int
    explanation: str

class OccupancyReconciler:
    def __init__(self, tolerance: int = 1):
        self.tolerance = tolerance

    def reconcile(
        self,
        classroom_id: str,
        vision_count: int,
        event_occupancy: int,
        identified_count: int,
        unknown_count: int = 0,
        uncertain_count: int = 0
    ) -> ReconciledOccupancyReport:
        diff = abs(vision_count - event_occupancy)
        unidentified = max(0, vision_count - identified_count)

        if diff == 0:
            status = "PERFECT_MATCH"
        elif diff <= self.tolerance:
            status = "MINOR_MISMATCH"
        else:
            status = "OCCUPANCY_MISMATCH"

        explanation = (
            f"{vision_count} people physically detected, {identified_count} identified students, "
            f"{unknown_count} unknown, {uncertain_count} uncertain. "
            f"Event occupancy: {event_occupancy} (Delta: {diff})."
        )

        return ReconciledOccupancyReport(
            classroom_id=classroom_id,
            vision_count=vision_count,
            event_occupancy=event_occupancy,
            identified_count=identified_count,
            unknown_count=unknown_count,
            uncertain_count=uncertain_count,
            difference=diff,
            status=status,
            unidentified_present=unidentified,
            explanation=explanation
        )
