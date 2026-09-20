"""FastAPI Application providing REST Endpoints, Event Streams, and Live WebSocket Dashboard updates."""
import asyncio
import json
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.events.event_schema import CampusEvent
from app.events.event_bus import default_event_bus
from app.backend.attendance_repository import AttendanceRepository
from app.backend.student_repository import StudentRepository
from app.backend.report_service import ReportService
from app.orchestration.campus_manager import CampusManager
from app.backend.schemas import (
    StudentProfileResponse,
    ClassroomStatusResponse,
    CampusSummaryResponse,
    ManualEventRequest
)

app = FastAPI(title="SRM AI Attendance System API", version="1.0.0")

# Shared singletons
attendance_repo = AttendanceRepository()
student_repo = StudentRepository()
campus_manager = CampusManager("configs/campus/campus_config.json")
report_service = ReportService(
    attendance_repo=attendance_repo,
    student_repo=student_repo,
    state_mgr=campus_manager.state_manager
)

# Connect Event Bus -> Persistence Repository
default_event_bus.subscribe("*", attendance_repo.save_event)

# Active WebSocket dashboard connections
active_connections: List[WebSocket] = []

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    dashboard_path = Path(__file__).resolve().parent.parent / "static" / "dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>Dashboard HTML not found</h2>")

@app.get("/api/campus/summary", response_model=CampusSummaryResponse)
async def get_campus_summary():
    telemetry = campus_manager.get_campus_telemetry()
    s = telemetry["summary"]
    return CampusSummaryResponse(
        campus_id=telemetry["campus_id"],
        total_enrolled=s["total_enrolled"],
        present_campus=s["present_campus"],
        outside_campus=s["outside_campus"],
        total_events=telemetry["accepted_events"],
        active_classrooms=telemetry["total_classrooms"]
    )

@app.get("/api/classrooms", response_model=List[ClassroomStatusResponse])
async def get_classrooms():
    telemetry = campus_manager.get_campus_telemetry()
    return [ClassroomStatusResponse(**r) for r in telemetry["classrooms"].values()]

@app.get("/api/students/{student_id}", response_model=StudentProfileResponse)
async def get_student_profile(student_id: str):
    meta = student_repo.get_student(student_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Student not found")

    st = campus_manager.state_manager.get_or_create(student_id)
    periods = report_service.evaluate_student_period_attendance(student_id, classroom_id=st.current_location)

    return StudentProfileResponse(
        student_id=meta.student_id,
        name=meta.name,
        department=meta.department,
        year=meta.year,
        current_location=st.current_location,
        state=st.state,
        entry_time=st.entry_time,
        last_seen=st.last_seen,
        accumulated_inside_sec=st.accumulated_inside_sec,
        periods=[p.to_dict() for p in periods]
    )

@app.get("/api/events/recent")
async def get_recent_events(limit: int = 50, event_type: Optional[str] = None):
    return attendance_repo.get_recent_events(limit=limit, event_type=event_type)

@app.post("/api/events/simulate")
async def simulate_event(req: ManualEventRequest):
    """Allows manual simulation of entry/exit crossing events for demo and verification."""
    event = CampusEvent.create_attendance(
        student_id=req.student_id,
        camera_id=req.camera_id,
        classroom_id=req.classroom_id,
        track_id=999,
        direction=req.direction,
        confidence=req.confidence
    )
    # 1. Publish to Event Bus
    default_event_bus.publish(event)
    # 2. Update Global Campus State
    campus_manager.receive_event(
        # Bridge to AttendanceEvent for backward compatibility
        event
    )
    return {"status": "SUCCESS", "event": event.to_dict()}

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    event_queue = default_event_bus.subscribe_async("*")
    try:
        # Send initial full state
        initial_telemetry = campus_manager.get_campus_telemetry()
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "telemetry": initial_telemetry,
            "recent_events": attendance_repo.get_recent_events(limit=15)
        })

        # Continuously stream real-time events to client
        while True:
            # Check for incoming events or periodic heartbeat
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=2.0)
                await websocket.send_json({
                    "type": "NEW_EVENT",
                    "event": event.to_dict(),
                    "summary": campus_manager.state_manager.get_campus_summary()
                })
            except asyncio.TimeoutError:
                # Heartbeat refresh
                await websocket.send_json({
                    "type": "HEARTBEAT",
                    "telemetry": campus_manager.get_campus_telemetry()
                })
    except WebSocketDisconnect:
        pass
    finally:
        default_event_bus.unsubscribe_async(event_queue)
        if websocket in active_connections:
            active_connections.remove(websocket)

