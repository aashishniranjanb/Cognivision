"""Candidate Verifier: Dual-tier verification comparing query against canonical centroid and multi-angle variant clusters."""
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from app.biometrics.repository import BiometricRepository
from app.face.candidate_retriever import RetrievedCandidate

@dataclass
class VerificationDecision:
    student_id: Optional[str]
    is_verified: bool
    decision: str  # "VERIFIED_MATCH", "UNCERTAIN", "AMBIGUOUS", "UNKNOWN_REJECTED"
    composite_similarity: float
    canonical_similarity: float
    best_variant_similarity: float
    best_matching_pose: str
    margin_to_second: float
    top_candidates: List[Dict[str, Any]] = field(default_factory=list)
    audit_notes: List[str] = field(default_factory=list)

class CandidateVerifier:
    def __init__(
        self,
        biometric_repo: Optional[BiometricRepository] = None,
        match_threshold: float = 0.68,
        uncertain_threshold: float = 0.55,
        min_margin: float = 0.04
    ):
        self.repo = biometric_repo or BiometricRepository()
        self.match_threshold = match_threshold
        self.uncertain_threshold = uncertain_threshold
        self.min_margin = min_margin

    def verify_candidates(
        self,
        query_embedding: np.ndarray,
        candidates: List[RetrievedCandidate],
        query_yaw: float = 0.0
    ) -> VerificationDecision:
        """Evaluates retrieved candidates against the canonical template and multi-angle variant cluster."""
        if not candidates:
            return VerificationDecision(
                student_id=None,
                is_verified=False,
                decision="UNKNOWN_REJECTED",
                composite_similarity=0.0,
                canonical_similarity=0.0,
                best_variant_similarity=0.0,
                best_matching_pose="NONE",
                margin_to_second=0.0,
                audit_notes=["No candidate retrieved from FAISS index"]
            )

        q_norm = np.array(query_embedding, dtype=np.float32).flatten()
        norm_val = np.linalg.norm(q_norm)
        if norm_val > 1e-6:
            q_norm = q_norm / norm_val

        # If query has head turn (> 12 degrees), give more weight to variant cluster
        if abs(query_yaw) > 12.0:
            alpha = 0.40  # 40% canonical, 60% variant
        else:
            alpha = 0.65  # 65% canonical, 35% variant

        verified_candidate_scores: List[Dict[str, Any]] = []

        for cand in candidates[:5]:
            # Fetch student's canonical template and variants from repository
            template_vec = self.repo.get_template_embedding(cand.student_id)
            variants = self.repo.get_variant_embeddings(cand.student_id)

            # 1. Canonical similarity
            if template_vec:
                t_arr = np.array(template_vec, dtype=np.float32)
                t_norm = np.linalg.norm(t_arr)
                if t_norm > 1e-6:
                    t_arr = t_arr / t_norm
                can_sim = float(np.dot(q_norm, t_arr))
            else:
                can_sim = cand.canonical_similarity or cand.max_similarity

            # 2. Best variant similarity
            if variants:
                var_sims = []
                for vid, v_emb, v_pose, v_qual in variants:
                    var_arr = np.array(v_emb, dtype=np.float32)
                    v_norm = np.linalg.norm(var_arr)
                    if v_norm > 1e-6:
                        var_arr = var_arr / v_norm
                    var_sims.append((float(np.dot(q_norm, var_arr)), v_pose))
                best_var_sim, best_pose = max(var_sims, key=lambda x: x[0])
            else:
                best_var_sim = can_sim
                best_pose = cand.best_matching_pose

            # 3. Composite multi-tier score
            composite = alpha * can_sim + (1.0 - alpha) * best_var_sim

            verified_candidate_scores.append({
                "student_id": cand.student_id,
                "composite": round(composite, 4),
                "canonical_sim": round(can_sim, 4),
                "variant_sim": round(best_var_sim, 4),
                "best_pose": best_pose
            })

        # Sort descending by composite score
        verified_candidate_scores.sort(key=lambda x: x["composite"], reverse=True)
        top = verified_candidate_scores[0]
        second = verified_candidate_scores[1] if len(verified_candidate_scores) > 1 else None

        margin = round(top["composite"] - second["composite"], 4) if second else 1.0
        audit_notes: List[str] = []

        # Decision Logic
        if top["composite"] < self.uncertain_threshold:
            decision = "UNKNOWN_REJECTED"
            is_verified = False
            audit_notes.append(f"Composite score {top['composite']:.3f} below uncertainty threshold {self.uncertain_threshold:.2f}")
            matched_id = None
        elif self.uncertain_threshold <= top["composite"] < self.match_threshold:
            decision = "UNCERTAIN"
            is_verified = False
            audit_notes.append(f"Composite score {top['composite']:.3f} within uncertainty band [{self.uncertain_threshold:.2f}, {self.match_threshold:.2f})")
            matched_id = top["student_id"]
        elif second and margin < self.min_margin:
            decision = "AMBIGUOUS"
            is_verified = False
            audit_notes.append(f"Ambiguous candidate: Margin to 2nd candidate {second['student_id']} ({margin:.3f}) below required {self.min_margin:.2f}")
            matched_id = top["student_id"]
        else:
            decision = "VERIFIED_MATCH"
            is_verified = True
            audit_notes.append(f"Verified match: Composite {top['composite']:.3f} >= {self.match_threshold:.2f}, Margin {margin:.3f}")
            matched_id = top["student_id"]

        return VerificationDecision(
            student_id=matched_id,
            is_verified=is_verified,
            decision=decision,
            composite_similarity=top["composite"],
            canonical_similarity=top["canonical_sim"],
            best_variant_similarity=top["variant_sim"],
            best_matching_pose=top["best_pose"],
            margin_to_second=margin,
            top_candidates=verified_candidate_scores,
            audit_notes=audit_notes
        )
