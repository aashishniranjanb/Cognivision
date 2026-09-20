"""Phase-II Scale Benchmark: 5 Classrooms, 10 Camera Feeds, 500 Students Concurrent Stream Processing."""
import time
import os
import sys
import psutil
import json
from typing import Dict, List
from pathlib import Path
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.orchestration.campus_manager import CampusManager
from app.attendance.event import AttendanceEvent

def run_phase2_campus_benchmark(
    config_path: str = "configs/campus/campus_config.json",
    num_students: int = 500,
    events_per_room: int = 100
) -> dict:
    print("=" * 75)
    print("  WEEK 6: PHASE-II 5 CLASSROOMS / 500 STUDENTS SCALE BENCHMARK")
    print("=" * 75)

    # 1. Initialize Campus Manager (Spawns 5 Classrooms, 10 Camera Workers)
    t_init_start = time.perf_counter()
    campus = CampusManager(config_path)
    campus.start_campus()
    t_init_ms = (time.perf_counter() - t_init_start) * 1000.0

    print(f" Campus Initialized : {campus.campus_id} ({len(campus.classrooms)} Classrooms, {len(campus.classrooms)*2} Cameras)")
    print(f" Initialization Time: {t_init_ms:.2f} ms")

    # 2. Simulate Concurrent Multi-Classroom Line Crossings
    print("-" * 75)
    print(f" Simulating {num_students} Students distributed across 5 Classrooms...")
    
    start_time = time.perf_counter()
    latencies = []
    
    # Generate 500 students (STU001 to STU500)
    student_ids = [f"STU{i:03d}" for i in range(1, num_students + 1)]
    classroom_keys = list(campus.classrooms.keys())

    # Step A: 500 Students Enter Assigned Classrooms at time T0
    track_id_counter = 1000
    t_sim_base = time.time()
    for idx, sid in enumerate(student_ids):
        target_room_id = classroom_keys[idx % len(classroom_keys)]
        room_mgr = campus.classrooms[target_room_id]

        t_evt_start = time.perf_counter()
        track_id_counter += 1
        # Entry camera detects and crosses line
        evt = room_mgr.entry_worker.simulate_crossing(
            track_id=track_id_counter,
            student_id=sid,
            confidence=0.92,
            timestamp=t_sim_base
        )
        evt_lat_ms = (time.perf_counter() - t_evt_start) * 1000.0
        latencies.append(evt_lat_ms)

    # Step B: 200 Students Exit their Classrooms (Normal Flow at T0 + 60s)
    t_exit_time = t_sim_base + 60.0
    for idx in range(200):
        sid = student_ids[idx]
        target_room_id = classroom_keys[idx % len(classroom_keys)]
        room_mgr = campus.classrooms[target_room_id]

        t_evt_start = time.perf_counter()
        track_id_counter += 1
        evt = room_mgr.exit_worker.simulate_crossing(
            track_id=track_id_counter,
            student_id=sid,
            confidence=0.91,
            timestamp=t_exit_time
        )
        evt_lat_ms = (time.perf_counter() - t_evt_start) * 1000.0
        latencies.append(evt_lat_ms)

    # Step C: Anti-Flap Stress Test (Attempt rapid contradictory entries at T_exit + 0.5s < 2.0s cooldown)
    t_flap_time = t_exit_time + 0.5
    flaps_attempted = 50
    for idx in range(flaps_attempted):
        sid = student_ids[idx] # These 50 students just exited
        target_room_id = classroom_keys[idx % len(classroom_keys)]
        room_mgr = campus.classrooms[target_room_id]

        track_id_counter += 1
        # Contradictory entry within <2.0s cooldown -> Should be suppressed by reconciler
        room_mgr.entry_worker.simulate_crossing(
            track_id=track_id_counter,
            student_id=sid,
            confidence=0.93,
            timestamp=t_flap_time
        )

    total_duration = time.perf_counter() - start_time
    total_events_processed = len(latencies) + flaps_attempted

    # Collect Telemetry
    telemetry = campus.get_campus_telemetry()
    campus.stop_campus()

    proc = psutil.Process(os.getpid())
    mem_mb = proc.memory_info().rss / (1024 * 1024)
    cpu_pct = psutil.cpu_percent(interval=0.1)

    avg_latency_ms = float(np.mean(latencies)) if latencies else 0.0
    p95_latency_ms = float(np.percentile(latencies, 95)) if latencies else 0.0
    p99_latency_ms = float(np.percentile(latencies, 99)) if latencies else 0.0
    throughput_eps = total_events_processed / max(0.001, total_duration)

    print("-" * 75)
    print(" PHASE-II PERFORMANCE RESULTS:")
    print(f"  Total Simulated Events    : {total_events_processed}")
    print(f"  Accepted Audited Events   : {telemetry['accepted_events']}")
    print(f"  Contradictory Flaps Dropped: {telemetry['rejected_conflicts']}")
    print(f"  Campus Event Throughput   : {throughput_eps:.1f} events/sec")
    print(f"  Avg Event Latency         : {avg_latency_ms:.2f} ms")
    print(f"  P95 Event Latency         : {p95_latency_ms:.2f} ms")
    print(f"  P99 Event Latency         : {p99_latency_ms:.2f} ms")
    print(f"  Process Memory RSS        : {mem_mb:.1f} MB")
    print(f"  Host CPU Utilization      : {cpu_pct:.1f}%")
    print("-" * 75)
    print(" ROOM OCCUPANCY BREAKDOWN:")
    for cid, r_stat in telemetry["classrooms"].items():
        print(f"  - {cid:<15} ({r_stat['name'][:22]:<22}): {r_stat['occupancy']:>3} / {r_stat['capacity']:>3} ({r_stat['occupancy_pct']:>5.1f}%)")
    print(f"  GLOBAL CAMPUS TOTAL: {telemetry['summary']['present_campus']} students currently inside campus rooms")
    print("=" * 75)

    return {
        "total_classrooms": telemetry["total_classrooms"],
        "total_cameras": telemetry["total_cameras"],
        "enrolled_students": num_students,
        "total_events_processed": total_events_processed,
        "accepted_events": telemetry["accepted_events"],
        "rejected_flaps": telemetry["rejected_conflicts"],
        "throughput_eps": round(throughput_eps, 1),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "p95_latency_ms": round(p95_latency_ms, 2),
        "p99_latency_ms": round(p99_latency_ms, 2),
        "memory_rss_mb": round(mem_mb, 1),
        "cpu_pct": round(cpu_pct, 1),
        "summary": telemetry["summary"],
        "classrooms": telemetry["classrooms"]
    }

if __name__ == "__main__":
    run_phase2_campus_benchmark()

