"""Inference Scheduler Benchmark: Compares Execution With vs Without Priority Selective Inference."""
import time
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.scheduling.priority_scheduler import PriorityInferenceScheduler, PriorityTier
from app.optimization.identity_cache import TrackIdentityCache

def benchmark_inference_scheduling(total_tracks: int = 100, frames: int = 100):
    print("=" * 70)
    print("  PHASE 13: PRIORITY INFERENCE SCHEDULER COMPUTATIONAL BENCHMARK")
    print("=" * 70)

    # 1. Baseline: Naive execution (Every track runs deep NN inference on every frame)
    t0 = time.perf_counter()
    naive_inferences = 0
    for f in range(frames):
        for tid in range(total_tracks):
            # Simulated neural inference time (e.g. 5ms per crop on CPU)
            time.sleep(0.0001)
            naive_inferences += 1
    t_naive = time.perf_counter() - t0

    # 2. Optimized: Priority Scheduler + TrackIdentityCache (Selective inference)
    t1 = time.perf_counter()
    cache = TrackIdentityCache(ttl_seconds=3.0)
    scheduler = PriorityInferenceScheduler(max_queue_size=200)
    selective_inferences = 0

    for f in range(frames):
        for tid in range(total_tracks):
            # Brand new tracks get Tier 2 (NEW_TRACK), confirmed get Tier 4 or bypass
            if cache.needs_recognition(tid):
                tier = PriorityTier.NEW_TRACK if tid not in cache.cache else PriorityTier.CONFIRMED_TTL
                scheduler.schedule(tid, "CAM_1", None, tier=tier)
            else:
                # Bypass inference completely on stable track
                pass

        # Pop scheduled tasks from priority queue
        while scheduler.pending_count() > 0:
            task = scheduler.get_next_task()
            time.sleep(0.0001) # Simulated neural inference
            selective_inferences += 1
            # Update cache to CONFIRMED
            cache.update(task.track_id, f"STU{task.track_id:03d}", 0.95, "CONFIRMED")

    t_selective = time.perf_counter() - t1

    reduction_pct = ((naive_inferences - selective_inferences) / naive_inferences) * 100.0
    speedup = t_naive / max(0.001, t_selective)

    print(f" Total Simulated Frames   : {frames}")
    print(f" Concurrent Tracks Seen   : {total_tracks}")
    print("-" * 70)
    print(f" Naive Deep Inferences    : {naive_inferences:,}")
    print(f" Naive Wall-Clock Time    : {t_naive:.3f} s")
    print("-" * 70)
    print(f" Selective Inferences Run : {selective_inferences:,}")
    print(f" Selective Wall-Clock Time: {t_selective:.3f} s")
    print("-" * 70)
    print(f" Neural Compute Reduction : {reduction_pct:.1f}%")
    print(f" Pipeline Throughput Gain : {speedup:.2f}x speedup")
    print("=" * 70)

    return {
        "naive_inferences": naive_inferences,
        "selective_inferences": selective_inferences,
        "compute_reduction_pct": round(reduction_pct, 1),
        "speedup": round(speedup, 2)
    }

if __name__ == "__main__":
    benchmark_inference_scheduling()

