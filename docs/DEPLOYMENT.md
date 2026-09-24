# SRM AI Automated Attendance System — On-Premise Deployment Guide

## 1. System Requirements & Hardware Sizing

| Component | Minimum Specification (5 Classrooms / 500 Students) | Recommended Production (10 Classrooms / 1000 Students) |
| :--- | :--- | :--- |
| **CPU** | Intel Core i7 12th Gen (8 cores / 16 threads) | Intel Xeon or AMD Ryzen 9 7900X (16 cores) |
| **RAM** | 16 GB DDR4/DDR5 | 32 GB DDR5 |
| **GPU** | NVIDIA RTX 3060 (12 GB VRAM) | NVIDIA RTX 4080 (16 GB) or 2x RTX 3060 |
| **Storage** | 256 GB NVMe SSD for OS + DB | 1 TB NVMe SSD (forensic event snapshots) |
| **Network** | 1 Gbps Dedicated CCTV VLAN | 2.5 Gbps or 10 Gbps Edge Switch |
| **OS** | Windows 10/11 Pro 64-bit or Ubuntu 22.04 LTS | Ubuntu 22.04 LTS or Windows Server 2022 |

---

## 2. Environment Configuration (`.env`)

Create `.env` inside the `ai-service/` root directory:

```env
# Server Network Settings
PORT=8000
HOST=0.0.0.0
WORKERS=1

# Camera Feeds & Hardware
CAMERA_URL=http://192.168.1.3:8080/video
RTSP_TRANSPORT=tcp
MAX_RTSP_LATENCY_MS=120

# Biometric & Processing Parameters
FACE_CONFIDENCE_THRESHOLD=0.70
FACE_MATCH_MARGIN=0.10
MIN_FACE_WIDTH_PX=80
MIN_LAPLACIAN_SHARPNESS=100.0

# Database & Storage
SQLITE_DB_PATH=campus_attendance.db
BACKUP_DIR=backups/
EVENT_RETENTION_DAYS=90

# Upstream Integration
SPRING_BOOT_FORWARDING=false
SPRING_BOOT_ENDPOINT=http://localhost:8080/api/attendance/events
```

---

## 3. Service Installation & Startup

### Step 1: Python Virtual Environment Setup
```powershell
cd "ai-service"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 2: Database Initialization & Roster Ingestion
```powershell
python -c "from app.backend.attendance_repository import AttendanceRepository; AttendanceRepository()._init_db()"
```

### Step 3: Frontend Production Build
```powershell
cd "..\attendance-frontend"
npm install
npm run build
```

### Step 4: Launching Production Services
```powershell
# Launch AI Backend Service
cd "..\ai-service"
python -m uvicorn app.backend.api:app --host 0.0.0.0 --port 8000
```

Access the Command Center UI at: `http://localhost:8000` (or `http://localhost:5173` via Vite dev server).

---

## 4. Health & Liveness Verification
Check service health before class periods:
- **Ping Liveness**: `GET http://localhost:8000/health`
- **System Telemetry**: `GET http://localhost:8000/api/system/status`
- **Camera Calibration**: `GET http://localhost:8000/api/cameras/survey`
