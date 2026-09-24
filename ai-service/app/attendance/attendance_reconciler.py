"""Attendance Reconciler: Reconciles physical presence, multi-session entries/exits,
and schedule intervals into transparent period attendance decisions.
Implements Step 6 of Plan 24.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import time

@dataclass
class PresenceInterval:
    entry_time: float
    exit_time: Optional[float] = None
    location_id: str = "CLASSROOM_203"
    confidence: float = 1.0

    @property
    def is_closed(self) -> bool:
        return self.exit_time is not None

    def overlap_seconds(self, period_start: float, period_end: float) -> float:
        """Calculates overlap in seconds between this interval and [period_start, period_end]."""
        end = self.exit_time if self.exit_time is not None else period_end
        effective_start = max(self.entry_time, period_start)
        effective_end = min(end, period_end)
        if effective_end > effective_start:
            return effective_end - effective_start
        return 0.0

@dataclass
class AttendanceDecision:
    student_id: str
    period_id: str
    location_id: str
    total_presence_seconds: float
    period_duration_seconds: float
    presence_ratio: float
    status: str            # "PRESENT", "PARTIAL", "ABSENT", "UNCERTAIN"
    sessions_count: int
    mean_confidence: float
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)

class AttendanceReconciler:
    def __init__(
        self,
        present_ratio_threshold: float = 0.75,   # e.g., >= 75% -> PRESENT
        partial_ratio_threshold: float = 0.15,   # e.g., 15% - 74% -> PARTIAL
        uncertain_confidence_threshold: float = 0.40
    ):
        self.present_ratio_threshold = present_ratio_threshold
        self.partial_ratio_threshold = partial_ratio_threshold
        self.uncertain_confidence_threshold = uncertain_confidence_threshold

        # student_id -> List[PresenceInterval]
        self.student_intervals: Dict[str, List[PresenceInterval]] = {}
        # student_id -> current open interval
        self.active_open_intervals: Dict[str, PresenceInterval] = {}

    def record_transition(
        self,
        student_id: str,
        direction: str,
        location_id: str,
        timestamp: float,
        confidence: float = 1.0
    ) -> Optional[PresenceInterval]:
        """
        Records an IN or OUT event for a student. Handles multi-session entry/re-entry.
        """
        if student_id not in self.student_intervals:
            self.student_intervals[student_id] = []

        if direction == "IN":
            if student_id in self.active_open_intervals:
                # Already inside; update location/confidence if changed
                interval = self.active_open_intervals[student_id]
                interval.location_id = location_id
                interval.confidence = max(interval.confidence, confidence)
                return interval

            interval = PresenceInterval(
                entry_time=timestamp,
                exit_time=None,
                location_id=location_id,
                confidence=confidence
            )
            self.active_open_intervals[student_id] = interval
            self.student_intervals[student_id].append(interval)
            return interval

        elif direction == "OUT":
            if student_id in self.active_open_intervals:
                interval = self.active_open_intervals.pop(student_id)
                interval.exit_time = timestamp
                return interval
            else:
                # OUT without open IN — create historical synthetic interval if desired or ignore
                return None

        return None

    def evaluate_student(
        self,
        student_id: str,
        period_id: str,
        period_start: float,
        period_end: float,
        location_id: str
    ) -> AttendanceDecision:
        """
        Evaluates a single student's attendance over a scheduled period.
        Accurately sums multiple presence intervals (e.g., temporary exit & re-entry).
        """
        period_duration = max(1.0, period_end - period_start)
        intervals = self.student_intervals.get(student_id, [])

        matching_intervals = [
            iv for iv in intervals
            if iv.location_id == location_id and iv.overlap_seconds(period_start, period_end) > 0
        ]

        total_presence = sum(iv.overlap_seconds(period_start, period_end) for iv in matching_intervals)
        ratio = min(1.0, total_presence / period_duration)

        if matching_intervals:
            conf_sum = sum(iv.confidence * iv.overlap_seconds(period_start, period_end) for iv in matching_intervals)
            mean_conf = conf_sum / total_presence if total_presence > 0 else 0.0
        else:
            mean_conf = 0.0

        sessions_count = len(matching_intervals)

        # Decision classification
        if mean_conf > 0 and mean_conf < self.uncertain_confidence_threshold:
            status = "UNCERTAIN"
            explanation = f"Confidence {mean_conf:.2f} is below reliability threshold ({self.uncertain_confidence_threshold:.2f})."
        elif ratio >= self.present_ratio_threshold:
            status = "PRESENT"
            explanation = f"Attended {total_presence/60:.1f}m of {period_duration/60:.1f}m ({ratio*100:.1f}%) across {sessions_count} session(s)."
        elif ratio >= self.partial_ratio_threshold:
            status = "PARTIAL"
            explanation = f"Partial attendance {total_presence/60:.1f}m of {period_duration/60:.1f}m ({ratio*100:.1f}%) across {sessions_count} session(s)."
        else:
            status = "ABSENT"
            if total_presence > 0:
                explanation = f"Brief presence {total_presence/60:.1f}m ({ratio*100:.1f}%) below minimum partial threshold ({self.partial_ratio_threshold*100:.0f}%)."
            else:
                explanation = "No valid physical presence recorded during period interval."

        return AttendanceDecision(
            student_id=student_id,
            period_id=period_id,
            location_id=location_id,
            total_presence_seconds=total_presence,
            period_duration_seconds=period_duration,
            presence_ratio=ratio,
            status=status,
            sessions_count=sessions_count,
            mean_confidence=mean_conf,
            explanation=explanation
        )

    def reconcile_period(
        self,
        period_id: str,
        period_start: float,
        period_end: float,
        location_id: str,
        roster: List[str]
    ) -> Dict[str, Any]:
        """
        Reconciles the entire roster for a specific period and location.
        Produces Four-Truths Attendance layer breakdown.
        """
        decisions: List[AttendanceDecision] = []
        counts = {"PRESENT": 0, "PARTIAL": 0, "ABSENT": 0, "UNCERTAIN": 0}

        # Check all enrolled students + any unexpected visitors detected
        detected_students = {
            sid for sid, ivs in self.student_intervals.items()
            if any(iv.location_id == location_id and iv.overlap_seconds(period_start, period_end) > 0 for iv in ivs)
        }
        all_eval_students = list(dict.fromkeys(roster + list(detected_students)))

        for sid in all_eval_students:
            dec = self.evaluate_student(sid, period_id, period_start, period_end, location_id)
            decisions.append(dec)
            if dec.status in counts:
                counts[dec.status] += 1

        return {
            "period_id": period_id,
            "location_id": location_id,
            "period_duration_minutes": (period_end - period_start) / 60.0,
            "expected_roster_count": len(roster),
            "evaluated_count": len(decisions),
            "present_count": counts["PRESENT"],
            "partial_count": counts["PARTIAL"],
            "absent_count": counts["ABSENT"],
            "uncertain_count": counts["UNCERTAIN"],
            "attendance_rate": (counts["PRESENT"] / len(roster)) if roster else 0.0,
            "decisions": [d.to_dict() for d in decisions]
        }
