"""
Sprint F Validation Suite:
- Task 32: 100 Students Scale Benchmark
- Task 33: 500 Students Scale Benchmark
- Task 34: 600+ Students Scale Benchmark
- Task 35: Different Lighting & Optical Quality Validation
"""

import time
import pytest
import numpy as np
import cv2

from app.face.index_manager import FaissIndexManager
from app.face.candidate_retriever import FaissCandidateRetriever
from app.face.candidate_verifier import CandidateVerifier
from app.face.confidence_calibrator import BiometricConfidenceCalibrator
from app.face.quality_evaluator import EnrollmentQualityEvaluator


class MockBiometricRepository:
    def __init__(self, student_dict):
        self.students = student_dict

    def get_template_embedding(self, student_id: str):
        if student_id in self.students:
            return self.students[student_id]["base"].tolist()
        return None

    def get_variant_embeddings(self, student_id: str):
        if student_id in self.students:
            vars_list = []
            for idx, v in enumerate(self.students[student_id]["variants"]):
                vars_list.append((idx + 1, v["vector"].tolist(), v["pose"], 0.92))
            return vars_list
        return []


def generate_synthetic_identity_cluster(rng: np.random.RandomState, num_variants: int = 5):
    """Generates a base 512-D unit vector and 5 coherent pose variants with cosine similarity >= 0.86."""
    base = rng.randn(512).astype(np.float32)
    base /= np.linalg.norm(base)

    variants = []
    poses = ["FRONTAL", "LEFT_PROFILE", "RIGHT_PROFILE", "TILT_UP", "TILT_DOWN"]

    for i in range(num_variants):
        noise = rng.randn(512).astype(np.float32)
        noise /= np.linalg.norm(noise)
        # 0.88 * base + 0.12 * noise maintains cos_sim approx 0.88
        vec = (0.88 * base + 0.12 * noise).astype(np.float32)
        vec /= np.linalg.norm(vec)
        variants.append({
            "pose": poses[i % len(poses)],
            "vector": vec
        })

    return base, variants


# ============================================================================
# Task 32: 100 Students Scale Benchmark
# ============================================================================
def test_100_students_scale_benchmark():
    rng = np.random.RandomState(101)
    num_students = 100
    manager = FaissIndexManager(dim=512)

    student_data = {}
    total_vectors = 0

    t0 = time.perf_counter()
    for i in range(num_students):
        sid = f"STU_100_{i:03d}"
        base, variants = generate_synthetic_identity_cluster(rng, num_variants=5)
        student_data[sid] = {"base": base, "variants": variants}

        for v in variants:
            manager.add_vector(sid, v["vector"], pose=v["pose"])
            total_vectors += 1

    build_time = time.perf_counter() - t0
    assert total_vectors == 500
    assert manager.index.ntotal == 500
    assert build_time < 2.0

    retriever = FaissCandidateRetriever(index_manager=manager, default_top_k=5)

    latencies = []
    correct_retrievals = 0

    test_sids = [f"STU_100_{i:03d}" for i in range(0, num_students, 2)]  # 50 students
    for sid in test_sids:
        base_probe = student_data[sid]["variants"][0]["vector"]
        noise = rng.randn(512).astype(np.float32)
        noise /= np.linalg.norm(noise)
        query = (0.95 * base_probe + 0.05 * noise).astype(np.float32)
        query /= np.linalg.norm(query)

        t_search = time.perf_counter()
        candidates = retriever.retrieve_candidates(query, top_k=5)
        lat = (time.perf_counter() - t_search) * 1000.0  # ms
        latencies.append(lat)

        assert len(candidates) > 0
        if candidates[0].student_id == sid:
            correct_retrievals += 1

    avg_latency = float(np.mean(latencies))
    p95_latency = float(np.percentile(latencies, 95))
    accuracy = correct_retrievals / len(test_sids)

    print(f"\n[Task 32] 100 Students (500 vectors): Avg Latency={avg_latency:.2f}ms, P95={p95_latency:.2f}ms, Accuracy={accuracy*100:.1f}%")
    assert avg_latency < 5.0
    assert accuracy >= 0.98


# ============================================================================
# Task 33: 500 Students Scale Benchmark
# ============================================================================
def test_500_students_scale_benchmark():
    rng = np.random.RandomState(505)
    num_students = 500
    manager = FaissIndexManager(dim=512)

    student_data = {}
    for i in range(num_students):
        sid = f"STU_500_{i:04d}"
        base, variants = generate_synthetic_identity_cluster(rng, num_variants=5)
        student_data[sid] = {"base": base, "variants": variants}

        for v in variants:
            manager.add_vector(sid, v["vector"], pose=v["pose"])

    assert manager.index.ntotal == 2500

    retriever = FaissCandidateRetriever(index_manager=manager, default_top_k=5)
    mock_repo = MockBiometricRepository(student_data)
    verifier = CandidateVerifier(biometric_repo=mock_repo, match_threshold=0.65)

    verification_latencies = []
    false_positives = 0
    true_positives = 0

    sample_sids = [f"STU_500_{i:04d}" for i in range(0, num_students, 17)][:30]
    for sid in sample_sids:
        # Genuine probe
        base_probe = student_data[sid]["variants"][1]["vector"]  # LEFT_PROFILE
        noise = rng.randn(512).astype(np.float32)
        noise /= np.linalg.norm(noise)
        query = (0.92 * base_probe + 0.08 * noise).astype(np.float32)
        query /= np.linalg.norm(query)

        t_start = time.perf_counter()
        candidates = retriever.retrieve_candidates(query, top_k=5)
        res = verifier.verify_candidates(query, candidates, query_yaw=-22.0)
        lat = (time.perf_counter() - t_start) * 1000.0
        verification_latencies.append(lat)

        if res.is_verified and res.student_id == sid:
            true_positives += 1

    # Impostor test: random unseen vectors
    for _ in range(10):
        impostor = rng.randn(512).astype(np.float32)
        impostor /= np.linalg.norm(impostor)

        candidates = retriever.retrieve_candidates(impostor, top_k=5)
        res = verifier.verify_candidates(impostor, candidates, query_yaw=0.0)
        if res.is_verified:
            false_positives += 1

    avg_lat = float(np.mean(verification_latencies))
    print(f"\n[Task 33] 500 Students (2,500 vectors): Avg End-to-End Latency={avg_lat:.2f}ms, TP={true_positives}/30, FP={false_positives}/10")
    assert avg_lat < 10.0
    assert true_positives >= 28
    assert false_positives == 0


# ============================================================================
# Task 34: 600+ Students Scale Benchmark (Production Grade)
# ============================================================================
def test_600_plus_students_scale_benchmark():
    rng = np.random.RandomState(650)
    num_students = 650  # 650 students exceeds 600+ specification
    manager = FaissIndexManager(dim=512)

    student_data = {}
    for i in range(num_students):
        sid = f"STU_650_{i:04d}"
        base, variants = generate_synthetic_identity_cluster(rng, num_variants=5)
        student_data[sid] = {"base": base, "variants": variants}

        for v in variants:
            manager.add_vector(sid, v["vector"], pose=v["pose"])

    # 650 students * 5 variants = 3,250 total indexed vectors
    assert manager.index.ntotal == 3250

    retriever = FaissCandidateRetriever(index_manager=manager, default_top_k=5)

    # Concurrency / batch query simulation: 50 concurrent corridor probe requests
    queries = []
    ground_truth = []
    test_indices = rng.choice(num_students, size=50, replace=False)

    for idx in test_indices:
        sid = f"STU_650_{idx:04d}"
        probe = student_data[sid]["variants"][0]["vector"]
        queries.append(probe)
        ground_truth.append(sid)

    t_batch = time.perf_counter()
    batch_hits = 0
    for q, target in zip(queries, ground_truth):
        cands = retriever.retrieve_candidates(q, top_k=5)
        if cands and cands[0].student_id == target:
            batch_hits += 1

    total_batch_time = (time.perf_counter() - t_batch) * 1000.0
    throughput_qps = 50.0 / (total_batch_time / 1000.0)

    print(f"\n[Task 34] 600+ Students (3,250 vectors): 50 Queries in {total_batch_time:.2f}ms ({throughput_qps:.1f} QPS), Top-1 Accuracy={batch_hits}/50")
    assert batch_hits == 50
    assert throughput_qps > 100.0


# ============================================================================
# Task 35: Different Lighting & Optical Quality Validation
# ============================================================================
def test_different_lighting_and_optical_conditions():
    evaluator = EnrollmentQualityEvaluator(min_face_width=70.0, min_blur_score=90.0)
    calibrator = BiometricConfidenceCalibrator()

    # 1. Optimal Ambient Lighting Image (112x112 synthetic face crop)
    optimal_crop = np.full((112, 112, 3), 140, dtype=np.uint8)
    cv2.circle(optimal_crop, (38, 42), 10, (40, 40, 40), -1)  # Left eye
    cv2.circle(optimal_crop, (74, 42), 10, (40, 40, 40), -1)  # Right eye
    cv2.circle(optimal_crop, (56, 62), 6, (90, 90, 90), -1)   # Nose
    cv2.line(optimal_crop, (36, 80), (76, 80), (30, 30, 30), 4) # Mouth
    cv2.line(optimal_crop, (40, 92), (72, 92), (60, 60, 60), 2) # Chin line
    noise = np.random.RandomState(42).randint(-25, 25, size=(112, 112, 3))
    optimal_crop = np.clip(optimal_crop.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    rep_optimal = evaluator.evaluate(optimal_crop)
    assert rep_optimal.is_acceptable is True
    assert rep_optimal.blur_score > 90.0
    assert rep_optimal.illumination_score > 0.40

    # Calibrated confidence for optimal condition
    conf_optimal = calibrator.calibrate(
        raw_cosine_similarity=0.78,
        face_width=112.0,
        blur_score=rep_optimal.blur_score,
        illumination_score=rep_optimal.illumination_score
    )
    assert conf_optimal >= 0.85

    # 2. Underexposed / Very Dark Lighting (mean brightness < 30)
    dark_crop = (optimal_crop * 0.15).astype(np.uint8)
    rep_dark = evaluator.evaluate(dark_crop)
    assert rep_dark.illumination_score < rep_optimal.illumination_score

    conf_dark = calibrator.calibrate(
        raw_cosine_similarity=0.78,
        face_width=112.0,
        blur_score=rep_dark.blur_score,
        illumination_score=rep_dark.illumination_score
    )
    # Calibration penalizes dark illumination
    assert conf_dark < conf_optimal

    # 3. Severe Motion Blur (Gaussian blur kernel 15x15)
    blurry_crop = cv2.GaussianBlur(optimal_crop, (15, 15), 5.0)
    rep_blurry = evaluator.evaluate(blurry_crop)
    assert rep_blurry.is_acceptable is False  # Fails gate because blur_score drops < 90
    assert rep_blurry.blur_score < 50.0

    conf_blurry = calibrator.calibrate(
        raw_cosine_similarity=0.78,
        face_width=112.0,
        blur_score=rep_blurry.blur_score,
        illumination_score=rep_blurry.illumination_score
    )
    assert conf_blurry < 0.60
