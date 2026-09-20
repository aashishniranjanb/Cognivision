# Week 2 Day 2: ByteTrack Multi-Object Tracking Benchmark Report

Date: 2026-09-20  
Environment: Intel(R) Core(TM) i5-9500 CPU @ 3.00GHz (6 Cores), 8GB RAM  
Detector: `yolov8n.pt` (Class `person` only)  
Tracker: `bytetrack.yaml` (`lap==0.5.13` linear assignment)  
Test Stream: Real Pedestrian CCTV footage (`pedestrians_sample.mp4`)  

---

## Benchmark Results (200 Sequential Frames)

| Metric | Measured Result | Production Target | Assessment |
| :--- | :--- | :--- | :--- |
| **Combined Tracking FPS** | **24.57 FPS** | > 15 FPS | **Real-time on CPU** |
| **Average Latency (Det + Track)** | **39.59 ms** | < 60 ms | Stable frame processing |
| **Active Track Persistence** | Persistent across 69 frames | No flicker | Stable track continuity |
| **ID Switch Failures** | **0 switches detected** | 0 on clean tracks | Track association maintained |
| **CPU Utilization** | **68.0%** | < 80% | Headroom preserved |
| **Process RAM (RSS)** | **387.5 MB** | < 1.0 GB | Highly lightweight footprint |

---

## Key Tracking Architectural Invariants

1. **Track ID $\neq$ Student ID**:
   - `Track ID` (e.g., `Track 01`) represents visual trajectory continuity across camera frames.
   - `Student ID` (e.g., `STU104`) will be bound to the track via downstream facial recognition (Week 3).
2. **Selective Downstream Inference**:
   - Instead of running face recognition on every frame (which would saturate CPU), recognition will only trigger selectively when a track is first established or periodically refreshed.
