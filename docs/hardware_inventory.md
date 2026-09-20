# Hardware & Environment Inventory

Generated: 2026-09-20
Project: AI Video Attendance System — Week 1 Foundation

## System Specifications

| Component | Specification | Notes |
| :--- | :--- | :--- |
| **Operating System** | Windows 11 Pro 64-bit | Local dev environment |
| **Processor (CPU)** | Intel(R) Core(TM) i5-9500 @ 3.00GHz | 6 Cores, 6 Logical Processors |
| **Installed RAM** | 7.83 GB | High memory pressure (~620MB free baseline). Keep frame queues bounded. |
| **Graphics (GPU)** | Intel(R) UHD Graphics 630 | Integrated GPU. Zero-copy frame buffers & CPU threading optimization applied. |
| **Storage** | Local SSD / HDD | Fast frame caching if needed |

## Runtime & Tooling

| Tool / Runtime | Installed Version | Target Requirement |
| :--- | :--- | :--- |
| **Python** | 3.14.0 | Python 3.10+ compatible |
| **Git** | 2.49.0 | Version control |
| **Node.js** | v25.1.0 | Dashboard (Week 4+) |
| **Java** | 1.8.0_401 | Spring Boot (Will upgrade to Java 21 LTS in Week 4) |
| **Docker** | Not installed | Host execution used for Phase I |

## Performance Engineering Constraints

1. **Queue Decoupling**: Because CPU is 6-core with integrated graphics, decoding CCTV frames must never run synchronously on the inference loop.
2. **Buffer Sizing**: Frame queues are capped to 15-30 frames per stream to preserve RAM and prevent latency drift (drop oldest strategy).
3. **Downscaling / ROI**: Frame monitoring runs at 720p or display-scaled dimensions to minimize CPU cache churn.
