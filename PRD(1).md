# AI Video-Based Attendance System --- Product Requirements Document (PRD)

**Project name:** Reliability-Aware Multimodal AI Video Attendance
System\
**Version:** 1.0\
**Date:** September 2026\
**Deployment target:** SRM Group institutional / campus environment\
**Primary constraint:** On-premise execution with zero cloud dependency

------------------------------------------------------------------------

## 1. Executive Summary

The system is an on-premise, CCTV-driven attendance platform designed to
automatically identify registered students/staff, track their movement
through entry/exit points, maintain classroom presence, and generate
period-level attendance.

The baseline recognition modality is facial recognition. The robustness
layer adds reliability-aware multimodal evidence from:

1.  Face recognition
2.  Person/body re-identification (Body Re-ID)
3.  Gait recognition, when a sufficiently long and usable walking
    sequence is available

Each available modality contributes two distinct signals:

-   **Identity evidence:** how strongly the current observation matches
    a candidate identity.
-   **Observation reliability:** how trustworthy the current observation
    is for recognition.

The Adaptive Fusion Engine converts reliability into dynamic modality
weights and combines candidate identity scores. A temporal identity
layer then stabilizes decisions across a person's track. Attendance is
marked only after identity and presence conditions are satisfied.

The architecture is intentionally modular: the competition can be
completed with a strong face-recognition + tracking core, while Body
Re-ID and Gait can be progressively enabled where they demonstrably
improve edge-case performance.

------------------------------------------------------------------------

## 2. Competition Requirements

The product must satisfy the following stated requirements:

### Core recognition

-   Identify registered students and staff from live or recorded CCTV.
-   Handle multiple people simultaneously.
-   Support entry and exit timestamps.
-   Calculate time spent inside designated areas.
-   Support period-level attendance.

### Edge cases

-   Face occlusion.
-   Low lighting.
-   Group movement.
-   Unknown persons.
-   Directional movement.
-   Temporary recognition failures.

### Phase I

-   At least 100 registered members.
-   Dual-camera setup: dedicated entry and exit cameras.
-   One classroom.
-   Live data capture.

### Phase II

-   At least 500 students.
-   Five classrooms simultaneously.
-   Architecture demonstrably scalable to campus-wide deployment.
-   1-week to 10-day live testing.

### Dashboard/reporting

-   Live room occupancy.
-   Class-by-class attendance status.
-   Daily reports.
-   Monthly reports.

### Deployment

-   Existing institutional infrastructure.
-   On-premise execution.
-   No cloud dependency.
-   Complete source-code handover.
-   Readable, documented code.

------------------------------------------------------------------------

## 3. Product Goals

### Primary goals

1.  Build a reliable CCTV-based attendance system.
2.  Achieve robust identity matching under real-world conditions.
3.  Correctly handle multiple simultaneous people.
4.  Maintain identity across frames using tracking.
5.  Produce auditable IN/OUT/PRESENT events.
6.  Support period-level attendance.
7.  Provide a live administrator dashboard.
8.  Demonstrate a credible path from 100 users / 1 room to 500+ users /
    5 rooms.
9.  Run entirely on institutional/on-premise infrastructure.
10. Provide an architecture that can be handed over to the SRM IT team.

### Secondary goals

-   Reduce unnecessary recognition inference through tracking and
    selective execution.
-   Use candidate retrieval rather than exhaustive comparison where
    scale requires it.
-   Add reliability-aware multimodal fusion for difficult observations.
-   Maintain an uncertainty state rather than forcing an identity.
-   Provide measurable diagnostics for model and camera failures.

------------------------------------------------------------------------

## 4. Non-Goals

The first release will NOT attempt to build:

-   A new foundation face-recognition model from scratch.
-   A new gait-recognition research model from scratch.
-   A global biometric identification system.
-   Cloud-based inference.
-   Continuous storage of raw CCTV video as the attendance database.
-   Voice-based attendance.
-   Emotion recognition.
-   Behavioral profiling.
-   Predictive attendance forecasting.
-   A large autonomous multi-agent AI architecture.
-   Campus-wide deployment before the single-room prototype is stable.

The system should focus on the stated attendance problem.

------------------------------------------------------------------------

## 5. Users

### 5.1 Administrator

Needs to:

-   Register/deactivate users.
-   View live occupancy.
-   View attendance.
-   Review uncertain/unknown events.
-   Correct attendance when authorized.
-   Generate daily/monthly reports.
-   Configure classrooms and schedules.
-   Monitor camera/system health.

### 5.2 Faculty

Needs to:

-   View current period attendance.
-   View absent/present students.
-   Review exceptions.
-   Export reports where authorized.

### 5.3 IT / Operations

Needs to:

-   Monitor inference nodes.
-   Monitor cameras.
-   Manage deployments.
-   Maintain databases and backups.
-   Review system logs.
-   Add classrooms/users.

### 5.4 Student/Staff

The system should only expose the minimum attendance information
required by institutional policy.

------------------------------------------------------------------------

## 6. Core Product Workflow

``` text
CCTV
  |
  v
Video Ingestion
  |
  v
Person Detection
  |
  v
Multi-Object Tracking
  |
  +-------------------+
  |                   |
  v                   v
Recognition        Track State
  |
  +-------------------------------+
  |               |               |
  v               v               v
Face             Body            Gait
  |               |               |
Identity         Identity        Identity
+ Reliability    + Reliability   + Reliability
  |               |               |
  +---------------+---------------+
                  |
                  v
       Reliability-Aware Fusion
                  |
                  v
       Temporal Identity Fusion
                  |
                  v
       Attendance State Machine
                  |
        +---------+----------+
        |                    |
        v                    v
    Attendance            Exception
       Event               / Unknown
        |
        v
   Backend/Event Bus
        |
   +----+-----+
   |          |
   v          v
Database   Dashboard
```

------------------------------------------------------------------------

## 7. Recognition Model Contract

Every modality should expose a common interface.

### Face

``` text
face_result = {
  candidate_id,
  identity_score,
  reliability_score,
  quality_features,
  timestamp,
  track_id
}
```

### Body Re-ID

``` text
body_result = {
  candidate_id,
  identity_score,
  reliability_score,
  quality_features,
  timestamp,
  track_id
}
```

### Gait

``` text
gait_result = {
  candidate_id,
  identity_score,
  reliability_score,
  quality_features,
  sequence_length,
  timestamp,
  track_id
}
```

The reliability score is NOT simply another identity score.

It represents the quality/trustworthiness of the observation.

------------------------------------------------------------------------

## 8. Reliability-Aware Adaptive Fusion

For candidate student `s` and modality `m`:

-   `S_m(s)` = identity similarity
-   `R_m` = current observation reliability
-   `B_m` = optional base importance of modality

A simple effective weight is:

``` text
E_m = B_m * R_m
```

and:

``` text
W_m = E_m / sum(E_j)
```

The fused score is:

``` text
S_fused(s) = sum(W_m * S_m(s))
```

Only available modalities participate.

### Example: normal conditions

``` text
Face:
  identity = 0.93
  reliability = 0.90

Gait:
  identity = 0.81
  reliability = 0.70

Body:
  identity = 0.87
  reliability = 0.80
```

Approximate normalized weights:

``` text
Face = 37.5%
Gait = 29.2%
Body = 33.3%
```

### Example: occluded face

``` text
Face:
  identity = 0.82
  reliability = 0.30

Gait:
  identity = 0.86
  reliability = 0.78

Body:
  identity = 0.84
  reliability = 0.75
```

The face contribution decreases while gait/body contributions increase.

### Important design rule

Do not hard-code:

``` text
Face = 70%
Gait = 15%
Body = 15%
```

as a universal rule.

Use measured quality/reliability and calibrate thresholds using
validation data.

------------------------------------------------------------------------

## 9. Reliability Estimation

### Face reliability features

Possible features:

-   Detection confidence.
-   Face bounding-box size.
-   Blur.
-   Illumination/exposure.
-   Pose angle.
-   Occlusion.
-   Alignment quality.
-   Facial landmark visibility.
-   Temporal consistency.

### Gait reliability features

Possible features:

-   Number of usable frames.
-   Pose/keypoint confidence.
-   Full-body visibility.
-   Walking consistency.
-   Temporal coverage.
-   Camera angle.
-   Track continuity.

### Body Re-ID reliability features

Possible features:

-   Bounding-box quality.
-   Resolution.
-   Body visibility.
-   Occlusion.
-   Viewpoint.
-   Segmentation quality.
-   Crop stability.
-   Track continuity.

The first implementation can use a calibrated deterministic quality
function. A learned reliability model can be introduced only if
benchmarking shows a benefit.

------------------------------------------------------------------------

## 10. Temporal Identity Confirmation

Attendance must not depend on a single frame.

For each person track:

``` text
Track 27
  t1 -> Student 104, confidence 0.88
  t2 -> Student 104, confidence 0.91
  t3 -> Student 104, confidence 0.86
  t4 -> Student 104, confidence 0.92
```

The system aggregates evidence over time.

A track can transition through:

``` text
UNKNOWN
   |
   v
TENTATIVE
   |
   v
CONFIRMED
   |
   v
PRESENT
```

If evidence becomes contradictory:

``` text
CONFIRMED
   |
   v
UNCERTAIN
```

Do not immediately replace a stable identity because of one poor frame.

------------------------------------------------------------------------

## 11. Attendance State Machine

Suggested states:

``` text
UNKNOWN
TENTATIVE
CONFIRMED
PRESENT
EXITED
UNCERTAIN
```

### Example rules

A candidate can become `CONFIRMED` when:

-   fused identity score exceeds a calibrated threshold;
-   identity is stable across multiple observations;
-   the track is valid;
-   the person is within the relevant region.

Attendance can become `PRESENT` when:

-   identity is confirmed;
-   person is inside the classroom/premises;
-   the event satisfies the configured period rule.

An exit event should not erase historical attendance. It should create
an auditable exit timestamp.

------------------------------------------------------------------------

## 12. Entry/Exit Requirements

Phase I requires:

``` text
Entry Camera ---> Entry Event
Exit Camera  ---> Exit Event
```

Each event should contain:

``` text
event_id
person_id
camera_id
location_id
direction
timestamp
track_id
confidence
event_type
```

Example:

``` json
{
  "person_id": "STU104",
  "camera_id": "ENTRY_CAM_01",
  "location_id": "CLASSROOM_203",
  "direction": "IN",
  "timestamp": "2026-10-07T09:02:17",
  "confidence": 0.88
}
```

------------------------------------------------------------------------

## 13. Period-Level Attendance

The system should maintain:

``` text
Academic day
  |
  +-- Period 1
  +-- Period 2
  +-- Period 3
  +-- ...
```

For each period:

``` text
Expected students
      |
      v
Presence evidence
      |
      v
Period attendance
```

A student who enters the campus but is not confirmed in the classroom
should not automatically receive classroom attendance.

------------------------------------------------------------------------

## 14. Unknown and Exception Handling

### Unknown person

If no candidate satisfies the identity threshold:

``` text
UNKNOWN
```

No attendance is marked.

### Uncertain identity

If multiple candidates have similar scores or modalities disagree:

``` text
UNCERTAIN
```

Continue collecting evidence.

### Camera failure

``` text
CAMERA_OFFLINE
```

Do not fabricate attendance.

### Model/inference failure

``` text
INFERENCE_DEGRADED
```

Record the incident.

------------------------------------------------------------------------

## 15. Dashboard Requirements

### Live dashboard

Must show:

-   Classroom.
-   Occupancy.
-   Present count.
-   Expected count.
-   Unknown count.
-   Uncertain count.
-   Entry/exit events.
-   Camera status.
-   AI processing status.

### Daily report

-   Student.
-   First entry.
-   Last exit.
-   Total duration.
-   Period attendance.
-   Exception count.

### Monthly report

-   Student.
-   Days present.
-   Days absent.
-   Attendance percentage.
-   Period-wise breakdown.

------------------------------------------------------------------------

## 16. Performance Targets

These are engineering targets, not guaranteed results.

### Phase I

-   100 registered users.
-   One room.
-   Two cameras.
-   Stable live tracking.
-   Reliable attendance event generation.

### Phase II

-   500 registered students.
-   Five classrooms.
-   Concurrent camera streams.
-   Central event processing.
-   Live dashboard.
-   No cloud dependency.

### Recognition metrics to measure

-   Identification accuracy.
-   False acceptance rate.
-   False rejection rate.
-   Unknown rejection rate.
-   Track ID switches.
-   Attendance precision.
-   Attendance recall.
-   Event timestamp error.
-   End-to-end latency.
-   FPS per camera.
-   GPU/CPU utilization.
-   Memory consumption.

------------------------------------------------------------------------

## 17. Acceptance Criteria

### Recognition

-   Registered users can be enrolled and retrieved.
-   Unknown users are not automatically assigned to known students.
-   Multiple people are tracked simultaneously.

### Attendance

-   Valid IN and OUT events are generated.
-   Period attendance is deterministic and auditable.
-   Duplicate attendance events are prevented.

### Edge cases

-   Face occlusion causes reduced face reliability rather than an
    unconditional identity failure.
-   Low lighting can trigger lower face reliability.
-   Unknown persons remain unknown.
-   Temporary modality failure does not immediately destroy an
    established track.

### Scalability

-   500-user database is supported.
-   Five-room architecture can be demonstrated.
-   Recognition search remains responsive as the database grows.

------------------------------------------------------------------------

## 18. Privacy and Security Requirements

Because the system processes biometric data:

-   Use minimum necessary data.
-   Encrypt sensitive data at rest and in transit.
-   Restrict administrative access.
-   Keep audit logs.
-   Define retention policies.
-   Avoid unnecessary raw-video retention.
-   Separate identity metadata from operational logs where practical.
-   Provide authorized deletion/deactivation workflows.
-   Follow applicable institutional policies and law.

------------------------------------------------------------------------

## 19. Product Success Definition

The project succeeds when it demonstrates:

> A locally deployed, scalable CCTV attendance platform that can
> identify registered people, maintain their tracks, produce auditable
> entry/exit/presence events, handle difficult visual conditions, and
> operate across multiple classrooms without requiring cloud services.

The multimodal fusion layer is an enhancement to robustness, not a
reason to delay the core attendance product.

------------------------------------------------------------------------

## 20. Recommended MVP Boundary

### Must have

-   Camera ingestion.
-   Person detection.
-   Multi-object tracking.
-   Face enrollment.
-   Face recognition.
-   Entry/exit logic.
-   Attendance database.
-   Live dashboard.
-   Daily/monthly reporting.
-   Unknown handling.
-   Basic quality/reliability estimation.

### Should have

-   Body Re-ID.
-   Reliability-aware fusion.
-   Temporal identity aggregation.
-   Exception review.

### Could have

-   Gait recognition.
-   Cross-camera identity continuity.
-   Advanced learned quality model.
-   Automatic camera-health diagnostics.

### Won't have in first release

-   Global campus deployment.
-   Complex research-only algorithms.
-   Cloud inference.
-   Large agent framework.

------------------------------------------------------------------------

# TECH STACK

See the separate `TECH_STACK.md` document for component-level technology
decisions.

# BUILD PLAN

See the separate `BUILD_PLAN.md` document for the six-week
implementation sequence.
