"""Scale Benchmark Suite: Evaluates FAISS Vector Retrieval and Adaptive Fusion Latency from 5 to 100 Students."""
import faiss
import numpy as np
import time
import psutil
import os
from typing import Dict

def benchmark_scale(n_students: int, vectors_per_student: int = 5, query_count: int = 500) -> dict:
    dim = 512
    total_vectors = n_students * vectors_per_student
    
    # Initialize FAISS FlatIP Index
    index = faiss.IndexFlatIP(dim)
    
    # Generate synthetic normalized embeddings for N students
    np.random.seed(42)
    embeddings = np.random.randn(total_vectors, dim).astype(np.float32)
    # L2 normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    
    # Index construction time
    t0 = time.perf_counter()
    index.add(embeddings)
    index_time_ms = (time.perf_counter() - t0) * 1000.0

    # Query speed test
    queries = np.random.randn(query_count, dim).astype(np.float32)
    q_norms = np.linalg.norm(queries, axis=1, keepdims=True)
    queries = queries / q_norms

    t1 = time.perf_counter()
    scores, indices = index.search(queries, k=1)
    total_query_time = time.perf_counter() - t1

    query_latency_us = (total_query_time / query_count) * 1_000_000.0 # Microseconds per search
    throughput_qps = query_count / total_query_time

    mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

    return {
        "enrolled_students": n_students,
        "total_vectors": total_vectors,
        "index_build_ms": round(index_time_ms, 2),
        "search_latency_us": round(query_latency_us, 2),
        "throughput_qps": round(throughput_qps, 1),
        "memory_rss_mb": round(mem_mb, 1)
    }

def run_scaling_benchmarks():
    print("=" * 65)
    print(" WEEK 5: FAISS RETRIEVAL SCALABILITY BENCHMARK (5 TO 100 STUDENTS)")
    print("=" * 65)
    print(f"{'Students':<10} | {'Vectors':<10} | {'Search Latency':<16} | {'Throughput':<14} | {'RAM (MB)':<10}")
    print("-" * 65)

    scales = [5, 10, 25, 50, 75, 100]
    results = []

    for n in scales:
        res = benchmark_scale(n_students=n, vectors_per_student=5, query_count=1000)
        results.append(res)
        print(f"{res['enrolled_students']:<10} | {res['total_vectors']:<10} | {res['search_latency_us']:<10} µs     | {res['throughput_qps']:<10} qps | {res['memory_rss_mb']:<10}")

    print("=" * 65)
    return results

def benchmark_phase2_scale(n_students: int = 500, vectors_per_student: int = 5, query_count: int = 2000) -> dict:
    """Week 6 Phase-II Scale: 500 Enrolled Students (2,500 512-D vectors in FAISS)."""
    print("=" * 70)
    print(f" WEEK 6 PHASE-II: {n_students} STUDENTS / 5 CLASSROOMS VECTOR RETRIEVAL SCALE")
    print("=" * 70)
    res = benchmark_scale(n_students=n_students, vectors_per_student=vectors_per_student, query_count=query_count)
    print(f"  Enrolled Students   : {res['enrolled_students']}")
    print(f"  Total Index Vectors : {res['total_vectors']}")
    print(f"  Index Construction  : {res['index_build_ms']} ms")
    print(f"  Vector Search Latency: {res['search_latency_us']} µs")
    print(f"  Throughput          : {res['throughput_qps']:.1f} QPS")
    print(f"  Process Memory RSS  : {res['memory_rss_mb']} MB")
    print("=" * 70)
    return res

if __name__ == "__main__":
    run_scaling_benchmarks()
    benchmark_phase2_scale()

