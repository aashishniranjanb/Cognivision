# SRM AI Automated Attendance System — System Architecture

## 1. System Overview
The SRM AI Automated Attendance System is an on-premise, zero-cloud edge intelligence platform designed to track and reconcile physical classroom attendance across multiple classrooms simultaneously. It uses edge CCTV streams, person detection, multi-object tracking, capture corridor selection, adaptive biometric fusion, and four-tier truth reconciliation.

```text
                     ┌────────────────────┐
                     │    SRM CCTV        │
                     │  10+ Camera Feeds  │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │  VIDEO INGESTION   │
                     │ RTSP + Resilience  │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │ PERSON DETECTION   │
                     │    YOLOv8-Nano     │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │    BYTE TRACK      │
                     └─────────┬──────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
             COUNT        CAPTURE ZONE     TRACK
                │              │              │
                │              ▼              │
                │        BEST FRAME           │
                │              │              │
                │       ┌──────┴──────┐       │
                │       ▼             ▼       │
                │     FACE           BODY     │
                │   (ArcFace)     (OSNet ReID)│
                │       └──────┬──────┘       │
                │              ▼              │
                │       ADAPTIVE FUSION       │
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                    ┌────────────────────┐
                    │ EVENT RECONCILIATION│
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │ GLOBAL STATE       │
                    │ INSIDE / OUTSIDE   │
                    └─────────┬──────────┘
                              ▼
                    ┌────────────────────┐
                    │ ATTENDANCE ENGINE  │
                    │ Period Rules (75%) │
                    └─────────┬──────────┘
                              ▼
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
          DASHBOARD        REPORTS       EVIDENCE
        (React Command)  (CSV / Audit)  (Forensic Drawer)
```

---

## 2. Core Pillars

### Pillar I: Controlled Capture Corridor
- **Problem**: Broad wide-angle doorway shots produce low-resolution, side-angle faces (< 50px) and erratic loitering.
- **Solution**: Virtual convex polygon corridor positioned 1.5m to 3.0m in front of the classroom door. Ensures face width $\ge 80$px, front-facing yaw $\le 30^\circ$, and continuous tracking trajectory across the crossing line vector.

### Pillar II: Adaptive Biometric Fusion
- **Face Embedding**: 512-D ArcFace embedding (Cosine similarity $\ge 0.50$ baseline, $\ge 0.70$ high confidence).
- **Body ReID**: 512-D OSNet appearance vector (Cosine similarity $\ge 0.65$).
- **Dynamic Weighting**: High face sharpness shifts weight toward face ($0.70 / 0.30$); face occlusion/blur shifts weight toward body appearance ($0.30 / 0.70$).
- **Zero False Acceptance Rate**: Reject ambiguous identities rather than misattributing attendance.

### Pillar III: Four Truths Architecture
1. **Physical Reality**: Total detected physical bodies crossing doorways and present inside classrooms.
2. **Biometric Identity**: Persons confirmed matched to enrolled student roster with high biometric certainty.
3. **Spatial Occupancy**: Headcounts inside each room reconciled against enrollment rosters (detects un-enrolled visitors and tailgating).
4. **Official Attendance**: Academic rule compliance requiring student presence for $\ge 75\%$ of the scheduled period session duration.

---

## 3. Technology Stack
- **AI Core**: Python 3.10+, PyTorch, Ultralytics YOLOv8, ByteTrack, InsightFace / ArcFace, FAISS vector search.
- **Backend Service**: FastAPI, Uvicorn, SQLite3 connection pool, asynchronous Event Bus, WebSocket broadcasting.
- **Frontend Dashboard**: React 18, Vite, Tailwind CSS, Lucide icons, responsive SVG charts.
