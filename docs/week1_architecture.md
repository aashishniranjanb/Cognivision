# Week 1 Architecture — Stream Ingestion & Decoupled Buffer

```
CCTV / Camera Sources
 (Webcam / RTSP / Video file / Synthetic Mock)
      │
      ▼
┌───────────────────────────────────────────────┐
│ Threaded StreamReader (app/camera/stream_reader)│
│  - Background grab thread (cv2.VideoCapture)  │
│  - FPS calculation (input rate)               │
│  - Health watchdog & auto-reconnection        │
└───────────────────────┬───────────────────────┘
                        │
                        ▼ (push frame + timestamp)
┌───────────────────────────────────────────────┐
│ Decoupled FrameBuffer (app/buffer/frame_buffer)│
│  - Thread-safe ring buffer (Bounded: ~30)     │
│  - Drop-oldest policy (prevents stale backlog)│
│  - Drop-counter & End-to-end Latency metrics  │
└───────────────────────┬───────────────────────┘
                        │
                        ▼ (pop latest frame)
┌───────────────────────────────────────────────┐
│ Consumer / Inference Queue (app/pipeline)     │
│  - Process frames asynchronously              │
│  - Overlay HUD diagnostic telemetry           │
│  - Prepares feed for Person Detection (Week 2)│
└───────────────────────────────────────────────┘
```

## Why Decoupled Buffering is Critical

1. **RTSP Buffer Bleed**: Without non-blocking threaded ingestion, a slow inference step (e.g. 15 FPS) will cause OpenCV/FFmpeg to buffer socket data in OS network buffers, introducing seconds of artificial lag.
2. **Drop-Oldest Strategy**: Real-time attendance requires current frames. If processing falls behind, dropping historical uninspected frames ensures the system always processes real-time events.
