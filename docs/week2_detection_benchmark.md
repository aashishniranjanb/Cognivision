# Week 2 Day 1: Person Detection Benchmark & Evaluation

Date: 2026-09-20  
Environment: Intel Core i5-9500 @ 3.00GHz (6 Cores), 8GB RAM, Intel UHD Graphics 630  
Model: `yolov8n.pt` (Nano model, PyTorch CPU runtime)  
Filtered Classes: `person` only (COCO class ID `0`)  

---

## Benchmark Results on Local Dev Machine

| Metric | Measured Result | Production Target | Assessment |
| :--- | :--- | :--- | :--- |
| **Input Resolution** | 1280 × 720 (720p) | 720p / 1080p | Standard CCTV resolution |
| **Detection Throughput** | **27.19 FPS** | > 15 FPS | **Excellent** (Near real-time on CPU) |
| **Average Latency** | **32.84 ms** | < 60 ms | Cleanly fits within a 33ms frame interval |
| **Min / Max Latency** | 29.0 ms / 59.8 ms | - | Stable across all test frames |
| **CPU Utilization** | **45.5%** | < 80% | Leaves headroom for tracking & video I/O |
| **Process RAM (RSS)**| **390.5 MB** | < 1.0 GB | Very low memory footprint |

---

## Key Takeaways

1. **CPU Viability Confirmed**: The Intel i5-9500 running YOLOv8n achieves **27.2 FPS** without a discrete GPU, meaning local development and Phase I testing with laptop webcams and recorded videos can run synchronously at near full 30 FPS.
2. **Decoupled Buffer Protection**: Even during peak inference spikes (59.8 ms), our decoupled `FrameBuffer` (maxsize=30, drop-oldest) protects the camera stream from any blocking or RTSP latency accumulation.
3. **Next Step**: Connect detections to **Multi-Object Tracking (ByteTrack / BoT-SORT)** to generate persistent `Track IDs` across frames.
