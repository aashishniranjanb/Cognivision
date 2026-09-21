# 10-Camera Full System Replay Benchmark Report

## Overview
- **Benchmark Type**: End-to-End Campus Replay (10 Concurrent CCTV Streams)
- **Cameras**: 10 Cameras (5 Classrooms, Paired ENTRY & EXIT)
- **Host Specs**: Windows 11, Intel Core Multi-Threaded Host, Python 3.14
- **Date**: 2026-09-21 01:51:22

## Throughput & Latency Performance
| Metric | Benchmark Result | Target / SLA | Status |
| :--- | :--- | :--- | :--- |
| **Total Frames Processed** | 400 | >= 400 | PASS |
| **Aggregate Pipeline FPS** | **25.6 FPS** | >= 15.0 FPS | PASS |
| **Per-Camera Effective Rate** | **2.56 FPS/cam** | >= 1.5 FPS/cam | PASS |
| **Average Event Latency** | **2.97 ms** | <= 100 ms | PASS |
| **P99 Event Latency** | **6.71 ms** | <= 200 ms | PASS |
| **Dropped Frames Rate** | **0.0%** | <= 1.0% | PASS |
| **ID Switch Rate** | **0.0%** | <= 0.5% | PASS |
| **False Acceptance Rate** | **0.0%** | <= 0.1% | PASS |

## Persistence & Audit Verification
- **Audited Events in SQLite**: 5 events
- **Immutable JSONL Audit Log**: `audit/attendance_audit.jsonl` synchronized
- **Reconciliation Conflicts**: 5 flapping attempts prevented
- **Host RAM RSS**: 443.5 MB
- **Host CPU Load**: 66.7%

## Period Timetable Evaluation
- **Timetable Schema**: 4 Academic Periods evaluated across all 5 classrooms
- **CSV Export Verification**: Generated 101 audited period rows
