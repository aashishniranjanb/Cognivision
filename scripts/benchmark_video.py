"""Comprehensive benchmarking script for recorded video and webcam streams."""
import sys
import os
import time
from pathlib import Path

# Add ai-service to path
sys.path.insert(0, os.path.abspath("ai-service"))

from app.camera.source import VideoSource
from app.pipeline.frame_queue import FrameBuffer, BufferedFrame
from app.metrics.ingestion_metrics import IngestionMetrics

def benchmark_video(video_path: str, max_frames: int = 150):
    print(f"--- Running Benchmark on Video: {video_path} ---")
    src = VideoSource(video_path, loop=True)
    buf = FrameBuffer(max_size=30)
    metrics = IngestionMetrics(window_sec=2.0)

    fps_vals = []
    latencies = []

    start = time.perf_counter()
    for i in range(max_frames):
        ret, frame = src.read()
        if not ret:
            break

        now = time.perf_counter()
        metrics.record_input()
        pkt = BufferedFrame(frame_id=i, timestamp=now, frame=frame, source_name="Benchmark")
        buf.put(pkt)

        # Consume
        out_pkt = buf.get(timeout=0.1)
        proc_now = time.perf_counter()
        latency = (proc_now - out_pkt.timestamp) * 1000.0
        metrics.record_processed(latency)

        if metrics.process_fps > 0:
            fps_vals.append(metrics.process_fps)
        latencies.append(latency)

    total_time = time.perf_counter() - start
    src.release()

    avg_fps = len(fps_vals) / total_time if total_time > 0 else 0
    min_fps = min(fps_vals) if fps_vals else 0
    max_fps = max(fps_vals) if fps_vals else 0
    avg_lat = sum(latencies) / len(latencies) if latencies else 0

    return {
        "resolution": f"{src.width()}x{src.height()}",
        "source_fps": src.fps(),
        "frames_tested": max_frames,
        "avg_fps": avg_fps,
        "min_fps": min_fps,
        "max_fps": max_fps,
        "avg_latency_ms": avg_lat,
        "dropped_frames": buf.dropped_frames
    }

if __name__ == "__main__":
    res = benchmark_video("ai-service/data/videos/test_video.mp4", max_frames=120)
    print("RESULTS:")
    for k, v in res.items():
        print(f"  {k}: {v}")
