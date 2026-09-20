"""Comprehensive Benchmark script for Person Detection + ByteTrack Multi-Object Tracking."""
import sys
import os
import time
import psutil
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.abspath("ai-service"))

from app.camera.source import VideoSource
from app.tracking.tracker import ByteTrackTracker

def benchmark_tracking(video_path: str, max_frames: int = 100):
    print(f"=== Running Detection + ByteTrack Benchmark on: {video_path} ===")
    src = VideoSource(video_path, loop=False)
    tracker = ByteTrackTracker(model_name="yolov8n.pt", conf_thresh=0.35, device="cpu")

    latencies = []
    active_track_counts = []
    track_occurrences = defaultdict(int)
    id_switches = 0
    prev_active_ids = set()

    process = psutil.Process(os.getpid())
    start_time = time.perf_counter()

    for idx in range(max_frames):
        ret, frame = src.read()
        if not ret or frame is None:
            break

        tracks, latency_ms = tracker.update(frame)
        latencies.append(latency_ms)
        active_track_counts.append(len(tracks))

        curr_active_ids = set()
        for t in tracks:
            curr_active_ids.add(t.track_id)
            track_occurrences[t.track_id] += 1

        prev_active_ids = curr_active_ids

    total_time = time.perf_counter() - start_time
    src.release()

    cpu_usage = psutil.cpu_percent()
    ram_mb = process.memory_info().rss / (1024 * 1024)

    avg_fps = len(latencies) / total_time if total_time > 0 else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    avg_active = sum(active_track_counts) / len(active_track_counts) if active_track_counts else 0

    print("\n" + "=" * 55)
    print("  WEEK 2 DAY 2: BYTE-TRACK MULTI-OBJECT TRACKING BENCHMARK")
    print("=" * 55)
    print(f"Frames Evaluated    : {len(latencies)}")
    print(f"Resolution          : {src.width()}x{src.height()}")
    print(f"Tracking FPS        : {avg_fps:.2f} FPS")
    print(f"Inference + Track ms: {avg_latency:.2f} ms")
    print(f"Min / Max Latency   : {min(latencies):.1f} ms / {max(latencies):.1f} ms")
    print(f"Total Unique Tracks : {len(tracker.total_tracks_seen)}")
    print(f"Avg Active Tracks   : {avg_active:.2f}")
    print(f"Track Lifespans     : {dict(track_occurrences)}")
    print(f"Process RAM RSS     : {ram_mb:.1f} MB")
    print(f"CPU Utilization     : {cpu_usage:.1f}%")
    print("=" * 55 + "\n")

    return {
        "frames": len(latencies),
        "fps": avg_fps,
        "latency_ms": avg_latency,
        "total_unique_tracks": len(tracker.total_tracks_seen),
        "ram_mb": ram_mb,
        "cpu_percent": cpu_usage
    }

if __name__ == "__main__":
    benchmark_tracking("ai-service/data/videos/multi_person_test.mp4", max_frames=80)
