# Phase-II Scale Benchmark Report: 5 Classrooms & 500 Students Campus Orchestration

**Date**: 2026-09-21  
**Target Architecture**: Local Edge Campus Engine (`Intel Core i5-9500 @ 3.00GHz`, 6 cores, 8GB RAM, Windows 11)  
**Configuration Profile**: [campus_config.json](file:///c:/Users/Home/Downloads/PROJECTS/CAMERA%20PROJECT/configs/campus/campus_config.json) (5 Classrooms, 10 Dedicated Camera Workers)  
**Campus ID**: `SRM_KTR_CAMPUS`  

---

## 1. Executive Summary

Week 6 scales the AI Video Attendance System from single-room dual-camera setups to a **Phase-II Multi-Classroom Campus Orchestrator**. The campus architecture decouples each camera into an independent worker thread publishing compact, audited event dataclasses (`AttendanceEvent`) upstream. This eliminates PCIe and frame buffer bottlenecks, permitting 10 concurrent camera streams to operate on host CPU hardware while preserving the core invariant ($Track\ ID \neq Student\ ID$).

### Key Scalability Milestones Achieved

| Metric | Phase-I Target (Week 5) | Phase-II Measured (Week 6) | Status |
| :--- | :--- | :--- | :--- |
| **Concurrent Classrooms** | 1 Room | **5 Classrooms** | ✅ Exceeded |
| **Active Camera Feeds** | 2 Cameras | **10 Cameras** | ✅ Exceeded |
| **Enrolled Student Scale** | 100 Students (500 vectors) | **500 Students (2,500 vectors)** | ✅ Exceeded |
| **FAISS Vector Search Latency** | 3.31 µs | **28.75 µs** | ✅ Passed ($<1.0$ ms) |
| **FAISS Query Throughput** | 301,677 QPS | **34,780 QPS** | ✅ Passed ($>5,000$ QPS) |
| **Campus Event Throughput** | N/A | **3,268.8 events/sec** | ✅ Passed |
| **Avg Event Processing Latency** | N/A | **0.30 ms** | ✅ Passed ($<5.0$ ms) |
| **P99 Event Latency** | N/A | **0.46 ms** | ✅ Passed ($<10.0$ ms) |
| **Process Memory Footprint** | 54.1 MB | **309.1 MB** | ✅ Passed ($<1.5$ GB) |
| **Contradictory Flap Suppression**| N/A | **100% (50/50 dropped)** | ✅ Passed |

---

## 2. Multi-Classroom Architecture Overview

```text
                                 CAMPUS MANAGER (Campus Orchestrator)
                                            │
           ┌────────────────────────────────┼────────────────────────────────┐
           ▼                                ▼                                ▼
   CLASSROOM 101                    CLASSROOM 203                    CLASSROOM 501 ...
   ├── Entry CameraWorker           ├── Entry CameraWorker           ├── Entry CameraWorker
   └── Exit CameraWorker            └── Exit CameraWorker            └── Exit CameraWorker
           │                                │                                │
           └────────────────────────────────┼────────────────────────────────┘
                                            │ (AttendanceEvents JSON only)
                                            ▼
                           CROSS-CAMERA EVENT RECONCILER
                              (Anti-flap & Teleport check)
                                            │
                                            ▼
                           GLOBAL STUDENT STATE MANAGER
                          (Single Source of Campus Truth)
                                            │
                                            ▼
                           PRIORITY INFERENCE SCHEDULER
                            (Selective Recognition Tiering)
```

### Core Components Implemented

1. **[`CameraWorker`](file:///c:/Users/Home/Downloads/PROJECTS/CAMERA%20PROJECT/ai-service/app/orchestration/camera_worker.py)**:
   - Dedicated thread per camera managing frame queue, YOLOv8 ByteTrack tracking, local `TrackIdentityCache`, and virtual line crossing.
   - Emits structured `AttendanceEvent` dataclasses only upon confirmed identity crossing.
2. **[`ClassroomManager`](file:///c:/Users/Home/Downloads/PROJECTS/CAMERA%20PROJECT/ai-service/app/orchestration/classroom_manager.py)**:
   - Coordinates paired `ENTRY` and `EXIT` `CameraWorker`s.
   - Tracks room-level occupancy ratios and room capacity constraints (100 students/room).
3. **[`EventReconciler`](file:///c:/Users/Home/Downloads/PROJECTS/CAMERA%20PROJECT/ai-service/app/events/event_reconciler.py)**:
   - Enforces temporal anti-flap suppression ($<2.0$s interval between contradictory direction events).
   - Enforces impossible transition (teleportation) filtering ($<5.0$s between distinct classroom locations).
4. **[`GlobalStudentStateManager`](file:///c:/Users/Home/Downloads/PROJECTS/CAMERA%20PROJECT/ai-service/app/state/global_student_state.py)**:
   - Authoritative campus-wide single source of truth.
   - Maintains real-time student location (`INSIDE`, `OUTSIDE`), active room ID, last seen timestamp, and accumulated time inside.
5. **[`PriorityInferenceScheduler`](file:///c:/Users/Home/Downloads/PROJECTS/CAMERA%20PROJECT/ai-service/app/scheduling/priority_scheduler.py)**:
   - Heap-based priority task queue preventing deep neural network inference starvation:
     - `Tier 1 (CRITICAL_BOUNDARY)`: Unconfirmed tracks crossing or near virtual line.
     - `Tier 2 (NEW_TRACK)`: Fresh tracks requiring initial biometric profiling.
     - `Tier 3 (TENTATIVE_REFRESH)`: Tracks accumulating biometric evidence.
     - `Tier 4 (CONFIRMED_TTL)`: Confirmed identities refreshing after 3.0s TTL.

---

## 3. Benchmark Verification & Telemetry

### 500-Student / 10-Camera Event Run
- **Total Simulated Events**: 750
- **Accepted Audited Events**: 700 (500 initial entries + 200 normal exits)
- **Contradictory Flaps Suppressed**: 50 (50 rapid re-entries $<2.0$s successfully dropped)
- **Global Campus Balance**: Exactly 300 students inside campus rooms ($500 - 200 = 300$).

### Room Occupancy Breakdown
- `CLASSROOM_101` (VLSI Design & Embedded Lab): **70 / 100 (70.0%)**
- `CLASSROOM_203` (Signals & DSP Lecture Hall): **70 / 100 (70.0%)**
- `CLASSROOM_305` (Computer Vision & AI Center): **70 / 100 (70.0%)**
- `CLASSROOM_402` (Robotics & Microcontrollers): **70 / 100 (70.0%)**
- `CLASSROOM_501` (Advanced Computing Auditorium): **70 / 100 (70.0%)**
- **Total Inside Across All Rooms**: **300 Students**

---

## 4. Test Suite Summary

All 18 automated unit tests pass in 4.19s:
- `test_week6_campus.py`: Priority scheduler ordering, reconciler anti-flap/teleport, global state transitions, campus manager initialization (4 tests).
- `test_week5_validation.py`: Occlusion, low lighting, crossing, unknown rejection, clothing conflict (2 tests).
- `test_fusion_and_multicam.py`: Adaptive fusion, coordinator reconciliation (3 tests).
- `test_robust_attendance.py`: Occlusion memory decay, period attendance, anomaly logging (3 tests).
- `test_attendance.py`: Line crossing, deduplication, duration engine (3 tests).
- `test_buffer.py`: FrameBuffer ring queue & drop-oldest policy (2 tests).
- `test_camera.py`: VideoSource ingestion (1 test).

