# Week 1 System Architecture: Ingestion & Telemetry

```
                  ┌──────────────────────────────┐
                  │        VIDEO SOURCES         │
                  └──────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
       [ Laptop Webcam (0) ]         [ Video File (.mp4) ]
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │   app/camera/source   │
                     │      VideoSource      │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │        Decoder        │
                     │    (cv2.VideoCapture) │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ app/pipeline/frame_q  │
                     │  FrameBuffer (max=30) │
                     │  (Drop-Oldest Policy) │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │    Inference Queue    │
                     │   (Decoupled Worker)  │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Live Preview Window  │
                     │  (960x540 + HUD Panel)│
                     └───────────┬───────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  ▼                             ▼
       ┌─────────────────────┐       ┌─────────────────────┐
       │ Ingestion Telemetry │       │ Structured Logs &   │
       │ (FPS, Latency, Q)   │       │ Event Stream        │
       └─────────────────────┘       └─────────────────────┘
```

## Key Invariants
1. **Threaded Decoupling**: Frame ingestion runs independently from the rendering/inference loop to prevent blocking.
2. **Drop-Oldest Queue Policy**: Guarantees real-time streaming by discarding oldest unconsumed frames when buffer overflows.
3. **Pluggable Source Design**: Any OpenCV-supported source (webcam index, file path, RTSP URL) can be passed into `VideoSource` without changing the rest of the application.
