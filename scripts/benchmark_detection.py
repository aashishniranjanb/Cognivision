"""Comprehensive Benchmark script for Person Detection on local CPU."""
import sys
import os
import time
import psutil
from pathlib import Path

sys.path.insert(0, os.path.abspath("ai-service"))

from app.camera.source import VideoSource
from app.detection.detector import PersonDetector

def run_detection_benchmark(video_path: str, max_frames: int = 60):
    print(f"=== Running Detection Benchmark on: {video_path} ===")
    src = VideoSource(video_path, loop=True)
    detector = PersonDetector(model_name="yolov8n.pt", conf_thresh=0.40, device="cpu")

    latencies = []
    people_counts = []
    fps_records = []

    process = psutil.Process(os.getpid())
    start_total = time.perf_counter()

    for idx in range(max_frames):
        ret, frame = src.read()
        if not ret:
            break

        detections, latency_ms = detector.detect(frame)
        latencies.append(latency_ms)
        people_counts.append(len(detections))
        fps_records.append(1000.0 / latency_ms if latency_ms > 0 else 0)

    total_time = time.perf_counter() - start_total
    src.release()

    cpu_usage = psutil.cpu_percent()
    ram_usage = process.memory_info().rss / (1024 * 1024)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    avg_fps = len(latencies) / total_time if total_time > 0 else 0
    avg_people = sum(people_counts) / len(people_counts) if people_counts else 0

    print("\n--- BENCHMARK RESULTS ---")
    print(f"Frames Evaluated    : {len(latencies)}")
    print(f"Resolution          : {src.width()}x{src.height()}")
    print(f"Source FPS          : {src.fps():.1f}")
    print(f"Avg Detection FPS   : {avg_fps:.2f} FPS")
    print(f"Avg Inference Latency: {avg_latency:.2f} ms")
    print(f"Min / Max Latency   : {min(latencies):.1f} ms / {max(latencies):.1f} ms")
    print(f"Avg Detected People : {avg_people:.2f} per frame")
    print(f"Process RAM RSS     : {ram_usage:.1f} MB")
    print(f"CPU Utilization     : {cpu_usage:.1f}%")
    print("-------------------------\n")

if __name__ == "__main__":
    run_detection_benchmark("ai-service/data/videos/test_video.mp4", max_frames=50)
