"""SRM AI Attendance System — One-Command Master Campus Runner.
Orchestrates 5 classrooms, 10 camera streams, real-time persistence,
health monitoring telemetry, and FastAPI executive dashboard.
"""
import sys
import os
import time
import random
import argparse
import signal
import threading
from pathlib import Path
import uvicorn

# Ensure ai-service root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.backend.api import app, campus_manager, attendance_repo, student_repo, report_service
from app.events.event_schema import CampusEvent
from app.events.event_bus import default_event_bus
from app.camera.health_monitor import default_health_monitor
from app.camera.stream_config import CameraConnectionState
from app.enrollment.registry import StudentRecord

stop_requested = threading.Event()

SAMPLE_STUDENTS = [
    StudentRecord("STU001", "Aditi Rao", "ECE", 3, True, "2026-09-01", 5),
    StudentRecord("STU002", "Rahul Sharma", "CSE", 3, True, "2026-09-01", 5),
    StudentRecord("STU003", "Priya Nair", "ECE", 2, True, "2026-09-01", 5),
    StudentRecord("STU004", "Karthik V", "Robotics", 4, True, "2026-09-01", 5),
    StudentRecord("STU005", "Sneha Patel", "AI & DS", 3, True, "2026-09-01", 5)
]

def seed_demo_roster():
    """Ensures base student registry contains enrolled student metadata."""
    for s in SAMPLE_STUDENTS:
        if s.student_id not in student_repo.registry.students:
            student_repo.registry.students[s.student_id] = s
    student_repo.registry.save()

def run_background_traffic_simulator(interval_sec: float = 4.0):
    """Generates realistic student arrivals and departures across classrooms for live demonstration."""
    classrooms = list(campus_manager.classrooms.keys())
    if not classrooms:
        classrooms = ["CLASSROOM_101", "CLASSROOM_203", "CLASSROOM_305", "CLASSROOM_402", "CLASSROOM_501"]

    track_counter = 100
    while not stop_requested.is_set():
        stop_requested.wait(interval_sec)
        if stop_requested.is_set():
            break

        stu = random.choice(SAMPLE_STUDENTS)
        cid = random.choice(classrooms)
        st = campus_manager.state_manager.get_or_create(stu.student_id)

        # Decide IN vs OUT based on current presence
        if st.state == "INSIDE" and st.current_location == cid:
            direction = "OUT"
            cam_id = f"EXIT_{cid.split('_')[-1]}"
        else:
            direction = "IN"
            cam_id = f"ENTRY_{cid.split('_')[-1]}"

        track_counter += 1
        conf = round(random.uniform(0.91, 0.98), 2)
        evt = CampusEvent.create_attendance(
            student_id=stu.student_id,
            camera_id=cam_id,
            classroom_id=cid,
            track_id=track_counter,
            direction=direction,
            confidence=conf
        )
        evt.metadata = {
            "face_confidence": conf,
            "face_quality": round(random.uniform(0.85, 0.94), 2),
            "face_reliability": "HIGH",
            "body_cosine": round(random.uniform(0.82, 0.91), 2),
            "body_reliability": "MEDIUM",
            "fused_score": round(conf * 0.7 + 0.26, 2)
        }

        # Process through campus reconciliation and event bus
        campus_manager.receive_event(evt)
        default_event_bus.publish(evt)

def main():
    parser = argparse.ArgumentParser(description="SRM AI Attendance Master System Runner")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve dashboard (default: 8000)")
    parser.add_argument("--demo", action="store_true", help="Enable synthetic pedestrian traffic simulator")
    parser.add_argument("--interval", type=float, default=5.0, help="Simulation traffic interval in seconds")
    args = parser.parse_args()

    print("=" * 75)
    print(" SRM AI MULTI-CAMERA ATTENDANCE SYSTEM — CAMPUS PRODUCTION ENGINE")
    print("=" * 75)
    print(f" Campus ID               : {campus_manager.campus_id}")
    print(f" Active Classrooms       : {len(campus_manager.classrooms)} rooms")
    print(f" Total Active Cameras    : {len(campus_manager.classrooms) * 2} cameras (Entry & Exit pairs)")
    print(f" Web Dashboard Interface : http://localhost:{args.port}/")
    print(f" CSV Report Export API   : http://localhost:{args.port}/api/reports/export/csv")
    print("=" * 75)

    # 1. Seed demo roster
    seed_demo_roster()

    # 2. Start all camera ingestion & worker threads
    print("[SystemRunner] Spawning 10 Camera Workers across 5 classrooms...")
    campus_manager.start_campus()

    # 3. Optional Background Traffic Simulator
    sim_thread = None
    if args.demo:
        print(f"[SystemRunner] Starting traffic simulator (interval: {args.interval}s)...")
        sim_thread = threading.Thread(
            target=run_background_traffic_simulator,
            args=(args.interval,),
            name="TrafficSimulator",
            daemon=True
        )
        sim_thread.start()

    # 4. Graceful Shutdown Handler
    def signal_handler(signum, frame):
        print("\n[SystemRunner] Received shutdown signal. Gracefully stopping campus engine...")
        stop_requested.set()
        campus_manager.stop_campus()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 5. Run Uvicorn HTTP + WebSocket server
    try:
        config = uvicorn.Config(app=app, host=args.host, port=args.port, log_level="info")
        server = uvicorn.Server(config)
        server.run()
    except KeyboardInterrupt:
        pass
    finally:
        print("[SystemRunner] Halting all camera workers and flushing audit logs...")
        stop_requested.set()
        campus_manager.stop_campus()
        print("[SystemRunner] Campus system shut down cleanly.")

if __name__ == "__main__":
    main()
