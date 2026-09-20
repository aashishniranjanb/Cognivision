# AI Video Attendance System --- Six-Week Build Plan

**Development window:** September 14, 2026 -- October 25, 2026\
**Phase I target:** October 7, 2026 --- 100 users, one room, dual
cameras\
**Phase II target:** October 25, 2026 --- 500 users, five rooms\
**Live testing:** October 26, 2026 onward

------------------------------------------------------------------------

# 1. Build Strategy

The project should be built in layers:

``` text
Layer 1 — Video
Layer 2 — Detection
Layer 3 — Tracking
Layer 4 — Face Recognition
Layer 5 — Attendance Events
Layer 6 — Dashboard
Layer 7 — Reliability
Layer 8 — Body Re-ID
Layer 9 — Gait
Layer 10 — Multi-room scaling
```

Do NOT begin by building all three recognition modalities
simultaneously.

The critical path is:

``` text
Camera
  ↓
Detection
  ↓
Tracking
  ↓
Face recognition
  ↓
Entry/exit
  ↓
Attendance
  ↓
Dashboard
```

Once this works reliably, add multimodal robustness.

------------------------------------------------------------------------

# 2. Week 1 --- Foundation and Camera Pipeline

## Objectives

Get real CCTV video into the system and establish a repeatable
development environment.

### Tasks

#### Infrastructure

-   Identify available GPU machine/server.
-   Record CPU, GPU, VRAM, RAM.
-   Verify drivers.
-   Install Python environment.
-   Install Java.
-   Install Node.js.
-   Install Docker.
-   Configure Git repository.

#### Camera

-   Obtain RTSP URLs or camera interface.
-   Verify entry camera.
-   Verify exit camera.
-   Measure resolution/FPS.
-   Test network stability.
-   Record short sample clips.

#### Video service

Build:

``` text
RTSP
 ↓
Decoder
 ↓
Frame buffer
 ↓
Inference queue
```

### Deliverables

-   Working camera stream.
-   Frame capture.
-   Sample video dataset.
-   Basic latency measurement.
-   Repository skeleton.
-   Initial architecture diagram.

### Exit criteria

The team can start the application and see the live camera stream
reliably.

------------------------------------------------------------------------

# 3. Week 2 --- Person Detection + Tracking

## Objectives

Track multiple people simultaneously.

### Tasks

-   Integrate person detector.
-   Integrate multi-object tracker.
-   Generate persistent track IDs.
-   Draw bounding boxes.
-   Test simultaneous entry.
-   Test simultaneous exit.
-   Test crossing people.
-   Measure ID switches.

Example:

``` text
Person A -> Track 12
Person B -> Track 18
Person C -> Track 21
```

### Important metrics

``` text
FPS
Latency
Active tracks
ID switches
Dropped frames
Detection confidence
```

### Deliverables

-   Multi-person live tracking.
-   Track IDs.
-   Track lifecycle.
-   Track entry/exit zones.

### Exit criteria

At least several simultaneous people can be tracked without the system
collapsing when people overlap.

------------------------------------------------------------------------

# 4. Week 3 --- Enrollment + Face Recognition

## Objectives

Build the first usable attendance identity system.

### Enrollment

Create an enrollment station:

``` text
Student
  ↓
Camera
  ↓
Face capture
  ↓
Quality check
  ↓
Embedding
  ↓
Database/vector index
```

Store:

``` text
student_id
name
department
face_template
template_version
status
```

### Recognition

``` text
Track
 ↓
Face detection
 ↓
Face embedding
 ↓
Top-K vector search
 ↓
Candidate identity
```

### Unknown handling

If no candidate exceeds the calibrated acceptance threshold:

``` text
UNKNOWN
```

### Deliverables

-   100-user enrollment.
-   Face embedding index.
-   Recognition API.
-   Unknown detection.
-   Recognition benchmark.

### Exit criteria

The system can enroll and recognize 100 people in the controlled Phase I
environment.

------------------------------------------------------------------------

# 5. Week 4 --- Attendance Engine + Phase I Demo

**Target:** October 7, 2026

## Objectives

Convert recognition into actual attendance.

### Entry logic

``` text
Entry camera
 ↓
Track
 ↓
Identity
 ↓
Virtual line/region
 ↓
IN event
```

### Exit logic

``` text
Exit camera
 ↓
Track
 ↓
Identity
 ↓
OUT event
```

### Database

Implement:

``` text
users
cameras
classrooms
attendance_events
attendance_records
periods
```

### Period attendance

Implement:

``` text
Classroom
+
Period
+
Confirmed presence
=
Attendance
```

### Dashboard v1

Display:

``` text
Present
Absent
Occupancy
Entry
Exit
Unknown
Camera status
```

### Phase I acceptance test

``` text
100 registered users
1 classroom
1 entry camera
1 exit camera
live attendance
```

### Deliverable

A stable demo that can be shown to mentors/HOD.

------------------------------------------------------------------------

# 6. Week 5 --- Reliability + Multimodal Layer

This week should focus on the competition's edge cases and innovation.

## 6.1 Face reliability

Implement quality features:

``` text
Detection confidence
Face size
Blur
Lighting
Pose
Occlusion
Alignment
```

Produce:

``` text
identity_score
reliability_score
```

### Example

``` text
Face identity = 0.92
Face reliability = 0.31
```

The system should interpret this as:

> High apparent match, but poor observation quality.

------------------------------------------------------------------------

## 6.2 Adaptive fusion

Implement:

``` text
effective_weight = base_weight × reliability
```

Normalize:

``` text
weight = effective_weight / sum(effective_weights)
```

Then:

``` text
fused_score = sum(weight × identity_score)
```

Initially support:

``` text
Face
Body
```

Add Gait only after its sequence pipeline is stable.

------------------------------------------------------------------------

## 6.3 Body Re-ID

Pipeline:

``` text
Person track
 ↓
Body crop
 ↓
Re-ID embedding
 ↓
Top-K candidate search
```

Reliability:

``` text
resolution
visibility
occlusion
viewpoint
crop quality
```

------------------------------------------------------------------------

## 6.4 Gait

Activate only when:

``` text
person is moving
+
sufficient frames
+
good pose quality
```

Pipeline:

``` text
Track
 ↓
Sequence buffer
 ↓
Pose
 ↓
Temporal model
 ↓
Gait embedding
```

------------------------------------------------------------------------

## 6.5 Temporal identity

Add:

``` text
Track history
 ↓
Identity smoothing
 ↓
Stable confirmation
```

This prevents a single bad frame from changing identity.

------------------------------------------------------------------------

# 7. Week 5 Testing Matrix

Build controlled test cases.

  Scenario                  Expected behavior
  ------------------------- -------------------------------
  Normal lighting           Face dominates
  Face partially occluded   Face reliability falls
  Heavy face occlusion      Body/gait may contribute
  Poor lighting             Face reliability falls
  Person walking            Gait becomes available
  Person standing           Gait unavailable
  Person seated             Gait disabled
  Body occlusion            Body reliability falls
  Unknown person            UNKNOWN
  Two similar candidates    UNCERTAIN until resolved
  Crowd crossing            Tracking maintains identities
  Camera interruption       CAMERA_OFFLINE

Do not claim improvement until measured.

------------------------------------------------------------------------

# 8. Week 6 --- Five-Classroom Scaling

## Target

``` text
500+ students
5 classrooms
multiple simultaneous streams
```

Architecture:

``` text
Room 1 ─┐
Room 2 ─┤
Room 3 ─┼──> AI/Event Layer ──> Database ──> Dashboard
Room 4 ─┤
Room 5 ─┘
```

### Tasks

-   Configure multiple camera streams.
-   Assign camera → classroom.
-   Run parallel inference workers.
-   Separate AI processing from backend.
-   Implement event queues.
-   Load test database.
-   Test dashboard under concurrent updates.
-   Measure GPU utilization.
-   Measure network bandwidth.
-   Measure end-to-end latency.

------------------------------------------------------------------------

# 9. Five-Classroom Load Test

Test at least:

``` text
5 rooms
2 cameras/room where available
multiple people/camera
500 registered identities
```

Measure:

``` text
Metric                    Target/goal
------------------------------------------------
Recognition latency       benchmark
Event latency             benchmark
Camera FPS                benchmark
GPU utilization           benchmark
VRAM usage                benchmark
CPU usage                 benchmark
Dropped frames            minimize
Track ID switches         minimize
Unknown rate              benchmark
False acceptance          benchmark
False rejection           benchmark
```

Do not invent target numbers before benchmarking the actual hardware.

------------------------------------------------------------------------

# 10. Dashboard v2

Final dashboard should contain:

## Campus view

``` text
Classroom 1    54/60
Classroom 2    48/55
Classroom 3    61/65
Classroom 4    52/58
Classroom 5    57/62
```

## Classroom view

``` text
Expected: 60
Present: 54
Absent: 5
Unknown: 1
Uncertain: 0
```

## Event feed

``` text
09:02:17  Student 104  ENTRY
09:02:19  Student 207  ENTRY
09:02:22  Unknown       ENTRY
09:03:04  Student 118  EXIT
```

## System health

``` text
Camera 1   ONLINE
Camera 2   ONLINE
GPU        72%
Queue      4
Database   ONLINE
```

------------------------------------------------------------------------

# 11. Exception Review

Create a review page:

``` text
UNKNOWN / UNCERTAIN EVENTS
```

Each event should show:

``` text
timestamp
camera
track
candidate ranking
face score
face reliability
body score
body reliability
gait score
gait reliability
fused score
```

This is valuable for debugging and for demonstrating the adaptive system
to judges.

------------------------------------------------------------------------

# 12. Benchmark Plan

Create a controlled evaluation dataset.

### Conditions

``` text
Normal
Low light
Face occlusion
Body occlusion
Side view
Crowd
Walking
Standing
Seated
Unknown person
```

### Compare

#### Baseline A

``` text
Face only
```

#### Baseline B

``` text
Fixed-weight Face + Body
```

#### Proposed

``` text
Reliability-aware Face + Body
```

#### Optional

``` text
Reliability-aware Face + Body + Gait
```

Measure:

``` text
Identification accuracy
FAR
FRR
Unknown rejection
Attendance precision
Attendance recall
Track stability
Latency
```

The most important experiment is:

> Does adaptive reliability weighting improve performance under edge
> cases compared with a fixed-weight baseline?

------------------------------------------------------------------------

# 13. Threshold Calibration

Do not select thresholds purely by intuition.

Use a validation set.

For example:

``` text
Training/calibration data
        ↓
Threshold sweep
        ↓
Precision/recall
        ↓
Choose operating point
        ↓
Freeze configuration
        ↓
Test on held-out data
```

Keep calibration data separate from final test data.

------------------------------------------------------------------------

# 14. Data Collection Plan

Collect representative samples with consent and institutional
authorization.

### Enrollment

For each person:

``` text
Several face samples
Several viewpoints
Short walking sequence
Body appearance samples
```

### Test conditions

Collect or simulate:

``` text
different lighting
partial occlusion
crowding
different distances
different viewpoints
walking
standing
seated
```

Avoid collecting unnecessary personal information.

------------------------------------------------------------------------

# 15. Team Allocation

For a 4--5 person team:

### Member 1 --- AI/Computer Vision

Own:

-   Detection.
-   Tracking.
-   Face recognition.
-   Body Re-ID.
-   Gait.

### Member 2 --- Fusion/ML

Own:

-   Reliability estimation.
-   Fusion.
-   Calibration.
-   Temporal aggregation.
-   Evaluation.

### Member 3 --- Backend

Own:

-   Spring Boot.
-   Database.
-   Attendance engine.
-   Event processing.
-   APIs.

### Member 4 --- Frontend

Own:

-   React dashboard.
-   Live monitoring.
-   Reports.
-   Exception review.

### Member 5 --- Infrastructure/Testing

Own:

-   CCTV.
-   GPU deployment.
-   Docker.
-   Performance testing.
-   Monitoring.
-   Documentation.

If only 3--4 members are available, merge Infrastructure into AI/Backend
and keep the core scope smaller.

------------------------------------------------------------------------

# 16. Git Workflow

Use:

``` text
main
develop
feature/*
fix/*
```

Recommended commits:

``` text
feat: add RTSP camera ingestion
feat: integrate person tracking
feat: implement face enrollment
feat: implement attendance event engine
feat: add face reliability estimation
feat: add body re-identification
feat: add adaptive fusion
feat: add live dashboard
perf: optimize multi-camera inference
test: add occlusion benchmark
```

Every major feature should have:

-   Code.
-   Test.
-   Documentation.
-   Demo evidence.

------------------------------------------------------------------------

# 17. Weekly Milestones

## Week 1

``` text
Camera → Frames
```

## Week 2

``` text
Frames → Tracks
```

## Week 3

``` text
Tracks → Identities
```

## Week 4

``` text
Identities → Attendance
```

## Week 5

``` text
Attendance → Robust multimodal system
```

## Week 6

``` text
Robust system → Five-classroom deployment
```

------------------------------------------------------------------------

# 18. Daily Development Loop

Every development day:

``` text
1. Define one measurable task
2. Implement
3. Test on real footage
4. Record metrics
5. Commit code
6. Update documentation
```

Do not spend several days only building UI before the recognition
pipeline works.

------------------------------------------------------------------------

# 19. Demo Strategy

## First video --- September 22

Keep it simple.

### 3--5 minutes

``` text
0:00–0:30 Problem
0:30–1:15 Architecture
1:15–2:15 Live recognition
2:15–3:00 Entry/exit
3:00–3:45 Edge-case handling
3:45–4:30 Dashboard
4:30–5:00 Scalability vision
```

Do not overload the first video with unfinished features.

------------------------------------------------------------------------

# 20. HOD Evaluation --- September 30

Show:

-   Working camera.
-   Multiple people.
-   Recognition.
-   Entry/exit.
-   Database.
-   Dashboard.
-   Initial metrics.
-   Known limitations.
-   Phase II plan.

Be transparent about what is complete.

------------------------------------------------------------------------

# 21. Phase I Demo --- October 7

Must demonstrate:

``` text
100 users
1 classroom
2 cameras
live attendance
entry/exit
dashboard
```

Recommended additional demonstration:

``` text
occlusion
unknown person
multiple people
```

------------------------------------------------------------------------

# 22. Final Showcase --- October 25

Demonstrate:

``` text
500+ students
5 classrooms
multiple simultaneous tracks
live dashboard
reports
edge-case handling
on-premise deployment
```

Show system metrics during the demo.

------------------------------------------------------------------------

# 23. Final Architecture Freeze

Before final deployment, freeze:

-   Model versions.
-   Embedding dimensions.
-   Database schema.
-   API contracts.
-   Thresholds.
-   Fusion formula.
-   Camera configuration.
-   Docker versions.
-   Hardware configuration.

Store everything in:

``` text
deployment/
docs/
configs/
```

------------------------------------------------------------------------

# 24. Documentation Package

Final handover should include:

``` text
README.md
ARCHITECTURE.md
PRD.md
TECH_STACK.md
BUILD_PLAN.md
DEPLOYMENT.md
API.md
DATABASE.md
MODEL_CARD.md
TEST_REPORT.md
BENCHMARKS.md
SECURITY.md
OPERATIONS.md
```

Also provide:

``` text
.env.example
docker-compose.yml
database migrations
configuration examples
startup scripts
```

Never include secrets in the repository.

------------------------------------------------------------------------

# 25. Final Risk Register

  -----------------------------------------------------------------------
  Risk                    Impact                  Mitigation
  ----------------------- ----------------------- -----------------------
  Face recognition weak   High                    Improve enrollment,
                                                  quality filtering,
                                                  Body/Gait fallback

  GPU insufficient        High                    Frame sampling,
                                                  batching, model
                                                  optimization

  Camera network unstable High                    Buffering, health
                                                  monitoring, reconnect

  Tracking ID switches    High                    Better tracker/camera
                                                  placement

  Gait pipeline too slow  Medium                  Run selectively

  Body Re-ID unreliable   Medium                  Treat as supporting
                                                  evidence

  Database overload       Medium                  Batch/event writes

  Too much scope          Very high               Protect MVP first

  Dashboard consumes time Medium                  Build only after
                                                  backend works

  Five-room scaling fails Very high               Start load testing
                                                  before Week 6

  Privacy/security issue  Very high               Minimize data, access
                                                  control, retention

  Thresholds overfit demo High                    Held-out test set
  data                                            
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 26. Hard Scope Rule

If a feature does not directly improve one of:

``` text
Recognition
Tracking
Attendance
Edge-case handling
Scalability
Dashboard/reporting
```

it should not be prioritized during the six-week competition.

------------------------------------------------------------------------

# 27. Definition of Done

The product is considered ready when:

``` text
[ ] 100-user Phase I works
[ ] Entry/exit works
[ ] Multiple people work
[ ] Unknown handling works
[ ] Attendance is auditable
[ ] Dashboard works
[ ] Reliability metrics work
[ ] Adaptive fusion is benchmarked
[ ] 500-user database works
[ ] Five-room architecture works
[ ] Load test completed
[ ] On-premise deployment reproducible
[ ] Source code documented
[ ] Handover documentation complete
```

------------------------------------------------------------------------

# 28. Final Principle

The project should be built as a **production-oriented attendance system
with a research-grade robustness layer**, not as a research demo that
happens to display attendance.

The order is:

``` text
RELIABLE CORE
     ↓
MEASURABLE BASELINE
     ↓
EDGE-CASE ROBUSTNESS
     ↓
ADAPTIVE FUSION
     ↓
MULTI-ROOM SCALE
     ↓
PRODUCTION HANDOVER
```

That ordering protects the competition deliverable while still giving
the project a technically distinctive component.
