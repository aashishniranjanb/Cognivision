"""Evaluation Metrics Engine: Calculates Precision, Recall, False Acceptance (FAR), False Rejection (FRR), and ID Switches."""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

@dataclass
class SystemMetricsReport:
    total_evaluations: int
    correct_identifications: int
    false_acceptances: int       # Wrong person identified
    false_rejections: int        # Enrolled person rejected / marked unknown
    true_unknown_rejections: int # Unknown person correctly marked unknown
    id_switches: int
    precision: float
    recall: float
    far: float                   # False Acceptance Rate
    frr: float                   # False Rejection Rate
    unknown_rejection_rate: float

class EvaluationMetricsEngine:
    def __init__(self):
        self.predictions: List[Tuple[Optional[str], Optional[str]]] = []  # (ground_truth_id, predicted_id)
        self.id_switches: int = 0

    def record_prediction(self, ground_truth_id: Optional[str], predicted_id: Optional[str]):
        """Records ground truth student_id vs system prediction (None = unknown)."""
        self.predictions.append((ground_truth_id, predicted_id))

    def record_id_switch(self):
        self.id_switches += 1

    def compute_report(self) -> SystemMetricsReport:
        total = len(self.predictions)
        if total == 0:
            return SystemMetricsReport(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

        correct = 0
        false_accept = 0
        false_reject = 0
        true_unknown = 0

        enrolled_cases = 0
        unknown_cases = 0

        for gt, pred in self.predictions:
            if gt is not None:  # Ground truth is an enrolled student
                enrolled_cases += 1
                if pred == gt:
                    correct += 1
                elif pred is None or pred == "UNKNOWN":
                    false_reject += 1
                else:
                    false_accept += 1
            else:  # Ground truth is an unknown person
                unknown_cases += 1
                if pred is None or pred == "UNKNOWN":
                    true_unknown += 1
                else:
                    false_accept += 1

        precision = correct / (correct + false_accept) if (correct + false_accept) > 0 else 0.0
        recall = correct / enrolled_cases if enrolled_cases > 0 else 0.0
        far = false_accept / (unknown_cases + enrolled_cases) if (unknown_cases + enrolled_cases) > 0 else 0.0
        frr = false_reject / enrolled_cases if enrolled_cases > 0 else 0.0
        unknown_rate = true_unknown / unknown_cases if unknown_cases > 0 else 1.0

        return SystemMetricsReport(
            total_evaluations=total,
            correct_identifications=correct,
            false_acceptances=false_accept,
            false_rejections=false_reject,
            true_unknown_rejections=true_unknown,
            id_switches=self.id_switches,
            precision=round(precision, 4),
            recall=round(recall, 4),
            far=round(far, 4),
            frr=round(frr, 4),
            unknown_rejection_rate=round(unknown_rate, 4)
        )
