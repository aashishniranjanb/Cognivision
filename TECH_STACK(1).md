# AI Video Attendance System --- Technical Stack

**Version:** 1.0\
**Deployment:** On-premise\
**Design principle:** Build a reliable modular system first; add
advanced multimodal capabilities only after measurable baseline
performance exists.

------------------------------------------------------------------------

## 1. Architecture

``` text
CCTV / RTSP
    |
    v
Video Ingestion
    |
    v
Frame Sampling / Preprocessing
    |
    v
Person Detection
    |
    v
Multi-Object Tracking
    |
    +------------------------------+
    |              |               |
    v              v               v
Face Pipeline   Body Re-ID      Gait Pipeline
    |              |               |
    +--------------+---------------+
                   |
                   v
        Reliability Estimation
                   |
                   v
        Adaptive Fusion Engine
                   |
                   v
        Temporal Identity Layer
                   |
                   v
         Attendance Event Engine
                   |
              Event/API Layer
                   |
       +-----------+------------+
       |                        |
       v                        v
    Database                Dashboard
```

------------------------------------------------------------------------

## 2. Recommended Stack Summary

  -----------------------------------------------------------------------
  Layer                   Recommended technology  Purpose
  ----------------------- ----------------------- -----------------------
  Camera                  RTSP-compatible CCTV    Video source

  Video decode            FFmpeg / GStreamer /    Stream handling
                          OpenCV                  

  Detection               YOLO-family detector or Person detection
                          equivalent              

  Tracking                ByteTrack / BoT-SORT    Multi-object tracking
                          class of tracker        

  Face embedding          ArcFace-class embedding Face representation
                          model                   

  Face search             FAISS or equivalent     Fast candidate
                          vector index            retrieval

  Face quality            OpenCV +                Reliability estimation
                          learned/calibrated FIQA 
                          if needed               

  Body Re-ID              OSNet / FastReID-class  Appearance embedding
                          approach                

  Gait                    Pose-based temporal     Walking-pattern
                          model / Gait            evidence
                          recognition model       

  Pose                    YOLO pose /             Gait features
                          MMPose-class approach   

  Fusion                  Python service          Dynamic weighting

  Backend                 Java Spring Boot        APIs, business logic,
                                                  attendance

  Event transport         Redis Streams /         Decoupling
                          RabbitMQ / Kafka-class  
                          broker                  

  Database                PostgreSQL or MySQL     Structured data

  Vector index            FAISS                   Embedding search

  Cache                   Redis                   Hot state/session/cache

  Frontend                React + TypeScript      Admin dashboard

  Charts                  Apache ECharts /        Analytics
                          Recharts                

  Deployment              Docker / Docker Compose Reproducible services
                          initially               

  Monitoring              Prometheus + Grafana    System metrics

  Logging                 Structured JSON logs    Debugging/audit

  API                     REST + WebSocket        Dashboard/event updates

  Testing                 Pytest + JUnit +        Automated tests
                          Playwright              

  Version control         Git + GitHub/GitLab     Source ownership
                          institutional           
                          repository              
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 3. Why Python for the AI Layer?

The computer-vision ecosystem is strongest in Python.

Python should own:

-   Video inference.
-   Detection.
-   Tracking integration.
-   Face embedding extraction.
-   Body Re-ID.
-   Gait inference.
-   Reliability calculation.
-   Fusion.
-   Candidate search.
-   AI metrics.

Suggested structure:

``` text
ai-service/
  app/
    api/
    detection/
    tracking/
    face/
    body_reid/
    gait/
    quality/
    fusion/
    identity/
    events/
    config/
```

The AI service should expose a clean API/event interface instead of
embedding business logic into model code.

------------------------------------------------------------------------

## 4. Why Spring Boot for Backend?

Spring Boot is appropriate for:

-   User management.
-   Classroom configuration.
-   Timetable/period logic.
-   Attendance rules.
-   Report generation.
-   Authorization.
-   Audit logging.
-   Administrative APIs.
-   Database transactions.
-   Integration with institutional IT systems.

Recommended modules:

``` text
backend/
  auth/
  users/
  classrooms/
  cameras/
  schedules/
  attendance/
  events/
  reports/
  audit/
  system/
```

Do not make Spring Boot perform heavy neural-network inference if the
Python AI stack already owns that workload.

------------------------------------------------------------------------

## 5. Frontend

Recommended:

``` text
React
TypeScript
Vite
```

Dashboard modules:

``` text
/dashboard
/users
/classrooms
/live
/attendance
/reports
/exceptions
/cameras
/system
```

Live updates should use WebSocket/SSE rather than constant polling.

------------------------------------------------------------------------

## 6. Database

### Recommended production choice

PostgreSQL is preferred if the team is free to choose.

MySQL is also acceptable if institutional familiarity or infrastructure
requires it.

### Core tables

``` text
users
biometric_templates
classrooms
cameras
periods
attendance_events
attendance_records
presence_tracks
exception_events
audit_logs
system_health
```

### Example

``` text
users
---------
id
institution_id
name
role
department
status
created_at

biometric_templates
---------
id
user_id
modality
embedding_reference
version
created_at
updated_at
```

Do not store all raw frames in these tables.

------------------------------------------------------------------------

## 7. Embedding Storage

Use vector indexes for retrieval.

Example:

``` text
Face embedding
      |
      v
FAISS index
      |
      v
Top-K candidates
```

For 500 users, exhaustive comparison may already be feasible depending
on embedding size and inference rate. FAISS becomes more valuable as the
number of enrolled users and cameras grows.

Do not introduce a vector database simply because the system contains
embeddings. Start with FAISS unless the scale and operational
requirements justify another system.

------------------------------------------------------------------------

## 8. Face Pipeline

``` text
Person track
    |
    v
Face detector
    |
    v
Face crop
    |
    v
Alignment
    |
    v
Face embedding
    |
    v
Vector search
    |
    v
Top-K candidates
    |
    v
Identity similarity
```

Parallel quality path:

``` text
Face crop
    |
    +--> Resolution
    +--> Blur
    +--> Illumination
    +--> Pose
    +--> Occlusion
    +--> Detection confidence
            |
            v
      Reliability score
```

------------------------------------------------------------------------

## 9. Body Re-ID Pipeline

``` text
Person track
    |
    v
Clean body crop
    |
    v
Re-ID embedding
    |
    v
Vector search
    |
    v
Candidate identity scores
```

Reliability features:

``` text
crop quality
resolution
visibility
occlusion
viewpoint
track stability
```

Body Re-ID should be treated as supporting evidence. Clothing changes
and viewpoint changes can reduce its reliability.

------------------------------------------------------------------------

## 10. Gait Pipeline

Gait should be activated only when sufficient motion data exists.

``` text
Track
  |
  v
Walking sequence
  |
  v
Pose/keypoints
  |
  v
Temporal feature extraction
  |
  v
Gait embedding
  |
  v
Candidate matching
```

Reliability depends on:

-   sequence length;
-   keypoint confidence;
-   visibility;
-   temporal continuity;
-   walking quality.

Do not run gait inference continuously on seated people.

------------------------------------------------------------------------

## 11. Adaptive Fusion

Suggested interface:

``` python
FusionInput(
    candidate_id,
    modality,
    identity_score,
    reliability_score,
    timestamp,
    track_id
)
```

Fusion:

``` python
effective = base_weight * reliability
weight = effective / sum(effective)
fused_score = sum(weight * identity_score)
```

Optional later upgrade:

``` text
softmax(beta * reliability)
```

Use calibration data to choose thresholds.

------------------------------------------------------------------------

## 12. Reliability Features

### Face

``` text
face_detection_confidence
face_width
face_height
blur_score
brightness_score
pose_score
occlusion_score
alignment_score
```

### Body

``` text
bbox_confidence
bbox_size
resolution
occlusion
viewpoint
crop_stability
segmentation_quality
```

### Gait

``` text
sequence_length
pose_confidence
visible_keypoint_ratio
motion_consistency
track_continuity
camera_angle
```

------------------------------------------------------------------------

## 13. Event Architecture

The AI layer should publish compact events instead of sending continuous
video to the backend.

Example:

``` json
{
  "event_type": "IDENTITY_OBSERVATION",
  "track_id": 27,
  "candidate_id": "STU104",
  "fused_score": 0.88,
  "modalities": {
    "face": {
      "identity": 0.93,
      "reliability": 0.90
    },
    "gait": {
      "identity": 0.81,
      "reliability": 0.70
    },
    "body": {
      "identity": 0.87,
      "reliability": 0.80
    }
  },
  "camera_id": "CAM_01",
  "timestamp": "2026-10-07T09:02:17"
}
```

The backend converts observations into business events such as:

``` text
ENTRY
EXIT
PRESENT
ABSENT
UNKNOWN
UNCERTAIN
CAMERA_OFFLINE
```

------------------------------------------------------------------------

## 14. Message Broker

### Phase I

Redis Streams can be sufficient and simple.

### Larger deployment

RabbitMQ or Kafka can be evaluated if event volume and operational
requirements justify them.

Do not start with Kafka unless needed. Complexity is a real cost in a
six-week build.

------------------------------------------------------------------------

## 15. API Design

### User APIs

``` text
POST   /api/users
GET    /api/users
GET    /api/users/{id}
PATCH  /api/users/{id}
DELETE /api/users/{id}
```

### Enrollment

``` text
POST /api/enrollment/start
POST /api/enrollment/{session}/capture
POST /api/enrollment/{session}/complete
```

### Attendance

``` text
GET /api/attendance/today
GET /api/attendance/student/{id}
GET /api/attendance/classroom/{id}
GET /api/attendance/period/{id}
```

### Live

``` text
GET /api/live/classrooms
GET /api/live/classrooms/{id}
```

### Reports

``` text
GET /api/reports/daily
GET /api/reports/monthly
```

------------------------------------------------------------------------

## 16. Authentication and Authorization

Minimum roles:

``` text
ADMIN
FACULTY
IT_OPERATOR
VIEWER
```

Use role-based access control.

Sensitive operations such as:

-   manual attendance correction;
-   user deletion/deactivation;
-   biometric enrollment;
-   system configuration

must be audited.

------------------------------------------------------------------------

## 17. On-Premise Deployment

Recommended:

``` text
                CAMPUS NETWORK
                      |
        +-------------+-------------+
        |                           |
   AI INFERENCE NODE          BACKEND SERVER
        |                           |
     GPU/CPU                    PostgreSQL
        |                           |
        +-------------+-------------+
                      |
                Dashboard clients
```

For five classrooms:

``` text
Room 1 -> AI worker
Room 2 -> AI worker
Room 3 -> AI worker
Room 4 -> AI worker
Room 5 -> AI worker
          |
          v
    Event/API layer
          |
          v
       Database
          |
          v
       Dashboard
```

Depending on hardware, multiple camera streams can share one inference
node.

------------------------------------------------------------------------

## 18. GPU Strategy

The system should not assume that every camera requires a dedicated GPU.

Benchmark:

``` text
1 camera
2 cameras
5 cameras
10 cameras
```

Measure:

-   FPS.
-   GPU utilization.
-   CPU utilization.
-   VRAM.
-   latency.
-   dropped frames.

Use batching where supported.

Use frame sampling carefully. Do not process every frame through every
expensive model.

------------------------------------------------------------------------

## 19. Performance Optimization

### Most important optimization

Do not run every model on every frame.

Use:

``` text
Detection
   |
Tracking
   |
Stable track?
   |
   +-- YES --> selective recognition
   |
   +-- NO --> full identity pipeline
```

### Additional optimizations

-   Resize frames appropriately.
-   Use detector batching where beneficial.
-   Cache embeddings.
-   Cache stable identities.
-   Use Top-K retrieval.
-   Run gait only when walking sequence exists.
-   Run face recognition periodically for stable tracks.
-   Use asynchronous queues.
-   Separate camera ingestion from inference.
-   Use GPU acceleration.
-   Avoid database writes for every frame.

------------------------------------------------------------------------

## 20. Monitoring

Use Prometheus/Grafana or an equivalent monitoring layer.

Track:

``` text
camera_fps
inference_latency
queue_depth
gpu_utilization
gpu_memory
cpu_utilization
ram_usage
dropped_frames
active_tracks
recognition_rate
unknown_rate
uncertain_rate
attendance_events
camera_disconnects
```

This is essential for the five-classroom demonstration.

------------------------------------------------------------------------

## 21. Logging

Use structured JSON logs.

Example:

``` json
{
  "timestamp": "...",
  "service": "fusion",
  "track_id": 27,
  "candidate_id": "STU104",
  "fused_score": 0.88,
  "decision": "CONFIRMED"
}
```

Never put raw biometric data or unnecessary personal information into
ordinary logs.

------------------------------------------------------------------------

## 22. Testing Stack

### AI

``` text
pytest
numpy
pandas
opencv
```

### Backend

``` text
JUnit
Spring Boot Test
Testcontainers
```

### Frontend

``` text
Vitest
React Testing Library
Playwright
```

### Load testing

``` text
k6 / Locust / JMeter
```

Test:

``` text
100 users
500 users
5 rooms
simultaneous tracks
camera interruptions
```

------------------------------------------------------------------------

## 23. Suggested Repository

``` text
ai-attendance/
|
├── ai-service/
├── backend/
├── frontend/
├── database/
├── deployment/
├── configs/
├── docs/
├── tests/
├── scripts/
└── README.md
```

### AI service

``` text
ai-service/
├── detection/
├── tracking/
├── face/
├── body_reid/
├── gait/
├── quality/
├── fusion/
├── identity/
├── events/
└── tests/
```

------------------------------------------------------------------------

## 24. Technology Selection Rule

Avoid technology for technology's sake.

### Use

``` text
Python + CV libraries
Spring Boot
React
PostgreSQL/MySQL
FAISS
Redis
Docker
```

### Add only if justified

``` text
Kafka
Kubernetes
advanced vector database
learned FIQA
distributed inference
```

The six-week goal is a functioning product, not a maximal infrastructure
diagram.

------------------------------------------------------------------------

# BUILD PLAN

See `BUILD_PLAN.md`.
