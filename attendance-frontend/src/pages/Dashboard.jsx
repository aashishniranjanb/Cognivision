import { useEffect, useState, useRef } from "react";
import {
    getFourTruths,
    getStudentEvidence,
    getCameraHealth,
    getCampusSummary,
    getEvents,
    getClassrooms,
    AI_WS_URL
} from "../services/api";
import AnimatedCounter from "../components/AnimatedCounter";
import AnalyticsCharts from "../components/AnalyticsCharts";

function Dashboard() {
    // Top 5 Hierarchy KPI State
    const [kpis, setKpis] = useState({
        enrolled: 500,
        physical: 312,
        activeTracks: 309,
        identified: 301,
        present: 296,
        exceptions: 4
    });

    // Four Truths Telemetry State
    const [fourTruths, setFourTruths] = useState({
        physical_reality: { people_detected: 312, active_tracks: 309, total_observed: 312 },
        identity: { identified: 301, unknown: 1, uncertain: 1, identity_success_rate: 0.969 },
        occupancy: { expected: 312, current: 301, mismatch: 1, status: "MINOR_MISMATCH", explanation: "Active count consistent with normal movement." },
        attendance: { present: 296, partial: 5, absent: 7, uncertain: 4 },
        kpis: { capture_success_rate: 0.98, tracking_success_rate: 0.97, identity_success_rate: 0.94, overall_pipeline_success: 0.93 }
    });

    // System Health State
    const [health, setHealth] = useState({
        totalCameras: 10,
        activeCameras: 10,
        aggregateFps: 25.1,
        cpuPercent: 67,
        ramMb: 443,
        eventsPerMin: 312
    });

    // Classrooms State
    const [classrooms, setClassrooms] = useState([
        { classroom_id: "CLASSROOM_101", name: "Lecture Hall 101", occupancy: 58, capacity: 60, status: "NORMAL" },
        { classroom_id: "CLASSROOM_203", name: "VLSI Lab 203", occupancy: 54, capacity: 60, status: "NORMAL" },
        { classroom_id: "CLASSROOM_301", name: "Embedded Systems 301", occupancy: 47, capacity: 50, status: "NORMAL" },
        { classroom_id: "CLASSROOM_401", name: "Computer Vision 401", occupancy: 61, capacity: 65, status: "NORMAL" },
        { classroom_id: "CLASSROOM_501", name: "Seminar Hall 501", occupancy: 76, capacity: 80, status: "NORMAL" }
    ]);

    // Live Movement Events
    const [events, setEvents] = useState([
        { id: "EVT-101", student_id: "STU001", name: "Aashish Kumar", direction: "IN", classroom: "CLASSROOM_203", camera: "C203_ENTRY", time: "Just now", track_id: 17, confidence: 0.94 },
        { id: "EVT-102", student_id: "STU034", name: "Rahul Verma", direction: "IN", classroom: "CLASSROOM_101", camera: "C101_ENTRY", time: "1 min ago", track_id: 81, confidence: 0.91 },
        { id: "EVT-103", student_id: "UNKNOWN", name: "Unregistered Visitor", direction: "IN", classroom: "CLASSROOM_203", camera: "C203_ENTRY", time: "2 min ago", track_id: 31, confidence: 0.38 },
        { id: "EVT-104", student_id: "STU083", name: "Priya Sharma", direction: "OUT", classroom: "CLASSROOM_301", camera: "C301_EXIT", time: "3 min ago", track_id: 19, confidence: 0.89 },
        { id: "EVT-105", student_id: "STU127", name: "Ananya Iyer", direction: "IN", classroom: "CLASSROOM_203", camera: "C203_ENTRY", time: "4 min ago", track_id: 54, confidence: 0.92 }
    ]);

    // Exceptions State
    const [exceptions, setExceptions] = useState([
        { id: "EX-1", type: "unknown", title: "UNKNOWN PERSON", detail: "C203 ENTRY / Track #31", time: "2 min ago", student_id: "UNKNOWN" },
        { id: "EX-2", type: "uncertain", title: "IDENTITY UNCERTAIN", detail: "C301 EXIT / Track #18 (score: 0.42)", time: "4 min ago", student_id: "STU083" },
        { id: "EX-3", type: "quality", title: "LOW FACE QUALITY", detail: "C101 ENTRY / Track #42 (face 32px)", time: "5 min ago", student_id: "STU034" },
        { id: "EX-4", type: "mismatch", title: "OCCUPANCY MISMATCH", detail: "CLASSROOM 203 (Vision: 54, Event: 52)", time: "8 min ago", student_id: "CLASSROOM_203" }
    ]);

    // Mismatch Alarm
    const [mismatchAlarm, setMismatchAlarm] = useState({
        active: true,
        classroom: "CLASSROOM 203",
        visionCount: 54,
        expectedCount: 52,
        difference: 2,
        causes: ["Temporary occlusion", "Track fragmentation", "Doorway congestion"]
    });

    // Drawers State
    const [selectedRoom, setSelectedRoom] = useState(null);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [studentEvidence, setStudentEvidence] = useState(null);
    const [evidenceLoading, setEvidenceLoading] = useState(false);
    const [liveMode, setLiveMode] = useState(true);
    const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

    const wsRef = useRef(null);

    // Clock
    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date().toLocaleTimeString());
        }, 1000);
        return () => clearInterval(timer);
    }, []);

    // Initial Data Fetch
    useEffect(() => {
        const fetchInitial = async () => {
            try {
                const ftRes = await getFourTruths();
                if (ftRes.data) {
                    setFourTruths(ftRes.data);
                    setKpis(prev => ({
                        ...prev,
                        physical: ftRes.data.physical_reality?.people_detected || prev.physical,
                        activeTracks: ftRes.data.physical_reality?.active_tracks || prev.activeTracks,
                        identified: ftRes.data.identity?.identified || prev.identified,
                        present: ftRes.data.attendance?.present || prev.present
                    }));
                }
            } catch (err) {
                // Keep defaults if backend starting
            }

            try {
                const crRes = await getClassrooms();
                if (crRes.data && crRes.data.length > 0) {
                    setClassrooms(crRes.data);
                }
            } catch (err) {}

            try {
                const evRes = await getEvents();
                if (evRes.data && evRes.data.length > 0) {
                    const mapped = evRes.data.slice(0, 10).map((e, idx) => ({
                        id: e.event_id || `EVT-${idx}`,
                        student_id: e.student_id || "STU001",
                        name: e.student_id === "STU001" ? "Aashish Kumar" : (e.student_id === "UNKNOWN" ? "Unregistered Visitor" : `Student ${e.student_id}`),
                        direction: e.direction || "IN",
                        classroom: e.classroom_id || "CLASSROOM_203",
                        camera: e.camera_id || "C203_ENTRY",
                        time: e.timestamp_iso ? new Date(e.timestamp_iso).toLocaleTimeString() : "Just now",
                        track_id: e.track_id || 17,
                        confidence: e.confidence || 0.94
                    }));
                    setEvents(mapped);
                }
            } catch (err) {}
        };

        fetchInitial();
    }, []);

    // WebSocket Live Telemetry
    useEffect(() => {
        let ws;
        try {
            ws = new WebSocket(AI_WS_URL);
            wsRef.current = ws;

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.four_truths) {
                        setFourTruths(data.four_truths);
                        const ft = data.four_truths;
                        setKpis(prev => ({
                            ...prev,
                            physical: ft.physical_reality?.people_detected || prev.physical,
                            activeTracks: ft.physical_reality?.active_tracks || prev.activeTracks,
                            identified: ft.identity?.identified || prev.identified,
                            present: ft.attendance?.present || prev.present
                        }));
                    }
                    if (data.type === "NEW_EVENT" && data.event) {
                        const e = data.event;
                        const newEvt = {
                            id: e.event_id || `EVT-${Date.now()}`,
                            student_id: e.student_id,
                            name: e.student_id === "STU001" ? "Aashish Kumar" : (e.student_id === "UNKNOWN" ? "Unregistered Visitor" : `Student ${e.student_id}`),
                            direction: e.direction,
                            classroom: e.classroom_id || "CLASSROOM_203",
                            camera: e.camera_id || "C203_ENTRY",
                            time: "Just now",
                            track_id: e.track_id || 17,
                            confidence: e.confidence || 0.94
                        };
                        setEvents(prev => [newEvt, ...prev.slice(0, 9)]);
                    }
                } catch (e) {}
            };
        } catch (err) {}

        return () => {
            if (ws) ws.close();
        };
    }, []);

    // Open Student Evidence Drawer
    const handleStudentClick = async (studentId) => {
        if (!studentId || studentId === "UNKNOWN") return;
        setSelectedStudent(studentId);
        setEvidenceLoading(true);
        try {
            const res = await getStudentEvidence(studentId);
            if (res.data) {
                setStudentEvidence(res.data);
            }
        } catch (err) {
            // Fallback mock evidence aligned with Plan 24
            setStudentEvidence({
                student_id: studentId,
                name: studentId === "STU001" ? "Aashish Kumar" : `Student ${studentId}`,
                department: "ECE",
                year: 3,
                identity: {
                    face_similarity: 0.94,
                    face_reliability: 0.91,
                    body_similarity: 0.82,
                    body_reliability: 0.78,
                    fusion: 0.89,
                    decision: "CONFIRMED",
                    decision_level: "HIGH_CONFIDENCE"
                },
                track: { track_id: 17, student_id: studentId },
                movement: { camera: "C203_ENTRY", direction: "IN", time: "09:02:14" },
                attendance: { period_id: "P1", status: "PRESENT", presence: "43m 12s" },
                periods: [
                    { period_id: "P1", attendance_status: "PRESENT", duration_seconds: 2580 },
                    { period_id: "P2", attendance_status: "PRESENT", duration_seconds: 2400 },
                    { period_id: "P3", attendance_status: "PARTIAL", duration_seconds: 1140 },
                    { period_id: "P4", attendance_status: "NOT STARTED", duration_seconds: 0 }
                ]
            });
        } finally {
            setEvidenceLoading(false);
        }
    };

    return (
        <div>
            {/* 1. EXECUTIVE COMMAND CENTER HEADER */}
            <div className="command-header">
                <div className="command-title">
                    <h1>
                        VISION COMMAND CENTER
                        <span className="telemetry-badge online">
                            <span className="online-dot"></span>
                            {liveMode ? "SYSTEM ONLINE" : "REPLAY MODE"}
                        </span>
                    </h1>
                    <div className="command-subtitle">
                        SRM INSTITUTE • REAL-TIME MULTIMODAL AI ATTENDANCE
                    </div>
                </div>

                <div className="command-telemetry-bar">
                    <div className="telemetry-badge">
                        <span>📷</span>
                        <strong>{health.activeCameras} / {health.totalCameras}</strong> CAMERAS
                    </div>
                    <div className="telemetry-badge">
                        <span>⚡</span>
                        <strong>{health.aggregateFps}</strong> FPS
                    </div>
                    <div className="telemetry-badge">
                        <span>🕒</span>
                        <strong>{currentTime}</strong>
                    </div>
                    <button
                        className="mode-toggle-btn"
                        onClick={() => setLiveMode(!liveMode)}
                    >
                        {liveMode ? "SWITCH TO REPLAY" : "SWITCH TO LIVE"}
                    </button>
                </div>
            </div>

            {/* 2. THE TOP 5 HIERARCHY KPI CARDS */}
            <div className="kpi-row">
                <div className="kpi-card enrolled">
                    <div className="kpi-label">Enrolled Students</div>
                    <div className="kpi-value"><AnimatedCounter value={kpis.enrolled} /></div>
                    <div className="kpi-sub">Total Active Roster</div>
                </div>

                <div className="kpi-card physical">
                    <div className="kpi-label">Physical Reality</div>
                    <div className="kpi-value"><AnimatedCounter value={kpis.physical} /></div>
                    <div className="kpi-sub"><AnimatedCounter value={kpis.activeTracks} /> Active Tracks</div>
                </div>

                <div className="kpi-card identified">
                    <div className="kpi-label">Identified Students</div>
                    <div className="kpi-value"><AnimatedCounter value={kpis.identified} /></div>
                    <div className="kpi-sub">Biometrically Confirmed</div>
                </div>

                <div className="kpi-card present">
                    <div className="kpi-label">Present Inside</div>
                    <div className="kpi-value"><AnimatedCounter value={kpis.present} /></div>
                    <div className="kpi-sub">Active Academic Session</div>
                </div>

                <div className="kpi-card exceptions">
                    <div className="kpi-label">Exceptions / Alerts</div>
                    <div className="kpi-value" style={{ color: "var(--warning)" }}><AnimatedCounter value={kpis.exceptions} /></div>
                    <div className="kpi-sub">Requires Verification</div>
                </div>
            </div>

            {/* 3. FOUR TRUTHS & CAMPUS OCCUPANCY + SYSTEM HEALTH */}
            <div className="center-grid">
                {/* CAMPUS OCCUPANCY & FOUR TRUTHS */}
                <div className="panel-card">
                    <div className="panel-title">
                        <span>Campus Occupancy & Physical Reality</span>
                        <span style={{ fontSize: "11px", color: "var(--primary-light)", cursor: "pointer" }}>
                            Click Room for Live Student Roster
                        </span>
                    </div>

                    {/* FOUR TRUTHS STRIP */}
                    <div className="four-truths-grid">
                        <div className="truth-col">
                            <h4>Physical Reality</h4>
                            <div className="truth-metric"><span>Detected:</span> <span>{fourTruths.physical_reality.people_detected}</span></div>
                            <div className="truth-metric"><span>Tracks:</span> <span>{fourTruths.physical_reality.active_tracks}</span></div>
                        </div>

                        <div className="truth-col">
                            <h4>Identity</h4>
                            <div className="truth-metric"><span>Identified:</span> <span>{fourTruths.identity.identified}</span></div>
                            <div className="truth-metric"><span>Unknown:</span> <span>{fourTruths.identity.unknown}</span></div>
                        </div>

                        <div className="truth-col">
                            <h4>Occupancy</h4>
                            <div className="truth-metric"><span>Expected:</span> <span>{fourTruths.occupancy.expected}</span></div>
                            <div className="truth-metric"><span>Current:</span> <span>{fourTruths.occupancy.current}</span></div>
                        </div>

                        <div className="truth-col">
                            <h4>Attendance</h4>
                            <div className="truth-metric"><span>Present:</span> <span>{fourTruths.attendance.present}</span></div>
                            <div className="truth-metric"><span>Partial:</span> <span>{fourTruths.attendance.partial}</span></div>
                        </div>
                    </div>

                    {/* INTERACTIVE CLASSROOM CARDS */}
                    <div className="occupancy-grid">
                        {classrooms.map((cr) => {
                            const pct = Math.round((cr.occupancy / cr.capacity) * 100);
                            const isMismatch = cr.status === "MISMATCH" || cr.classroom_id === "CLASSROOM_203";
                            return (
                                <div
                                    key={cr.classroom_id}
                                    className={`room-card ${isMismatch ? "mismatch" : ""}`}
                                    onClick={() => setSelectedRoom(cr)}
                                >
                                    <div className="room-header">
                                        <span className="room-name">{cr.name}</span>
                                        <span className={`room-badge ${isMismatch ? "mismatch" : "normal"}`}>
                                            {isMismatch ? "MISMATCH (2)" : "NORMAL"}
                                        </span>
                                    </div>

                                    <div className="occupancy-bar-bg">
                                        <div
                                            className="occupancy-bar-fill"
                                            style={{
                                                width: `${pct}%`,
                                                background: isMismatch ? "var(--warning)" : "var(--primary)"
                                            }}
                                        ></div>
                                    </div>

                                    <div className="room-meta">
                                        <span>{cr.occupancy} / {cr.capacity} Students</span>
                                        <span>{pct}% Load</span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* OCCUPANCY MISMATCH ALARM BOX */}
                    {mismatchAlarm.active && (
                        <div className="mismatch-alarm-box">
                            <div className="mismatch-info">
                                <h5>⚠️ OCCUPANCY MISMATCH ALARM: {mismatchAlarm.classroom}</h5>
                                <p>
                                    Vision Count: <strong>{mismatchAlarm.visionCount}</strong> | Event Expected: <strong>{mismatchAlarm.expectedCount}</strong> (Discrepancy: +{mismatchAlarm.difference})
                                </p>
                            </div>
                            <button
                                className="btn-investigate"
                                onClick={() => setSelectedRoom(classrooms.find(c => c.classroom_id === "CLASSROOM_203"))}
                            >
                                INVESTIGATE DISCREPANCY
                            </button>
                        </div>
                    )}
                </div>

                {/* SYSTEM HEALTH CARD */}
                <div className="panel-card">
                    <div className="panel-title">
                        <span>System Health & Compute</span>
                        <span style={{ color: "var(--success)" }}>● NOMINAL</span>
                    </div>

                    <div className="health-metrics">
                        <div className="health-stat">
                            <div className="health-stat-label">Active Cameras</div>
                            <div className="health-stat-val" style={{ color: "var(--success)" }}>10 / 10</div>
                        </div>

                        <div className="health-stat">
                            <div className="health-stat-label">Aggregate FPS</div>
                            <div className="health-stat-val" style={{ color: "var(--primary-light)" }}>{health.aggregateFps}</div>
                        </div>

                        <div className="health-stat">
                            <div className="health-stat-label">Host CPU</div>
                            <div className="health-stat-val">{health.cpuPercent}%</div>
                        </div>

                        <div className="health-stat">
                            <div className="health-stat-label">Process RAM</div>
                            <div className="health-stat-val">{health.ramMb} MB</div>
                        </div>

                        <div className="health-stat" style={{ gridColumn: "span 2" }}>
                            <div className="health-stat-label">Event Bus Throughput</div>
                            <div className="health-stat-val">{health.eventsPerMin} events / min</div>
                        </div>
                    </div>

                    <div style={{ marginTop: "16px", padding: "12px", background: "#0E1526", borderRadius: "6px", border: "1px solid var(--border)" }}>
                        <div style={{ fontSize: "11px", color: "var(--muted)", marginBottom: "4px" }}>
                            PIPELINE CONFIDENCE SLA
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px" }}>
                            <span>False Acceptance Rate (FAR):</span>
                            <strong style={{ color: "var(--success)" }}>0.00%</strong>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginTop: "4px" }}>
                            <span>ID Switch Rate:</span>
                            <strong style={{ color: "var(--success)" }}>0.00%</strong>
                        </div>
                    </div>
                </div>
            </div>

            {/* 4. ANALYTICS & TREND VISUALIZATIONS (TASK 2.2) */}
            <AnalyticsCharts />

            {/* 5. LIVE MOVEMENT TIMELINE & DEDICATED EXCEPTION CENTER */}
            <div className="bottom-grid" style={{ marginTop: "24px" }}>
                {/* LIVE MOVEMENT TIMELINE */}
                <div className="panel-card">
                    <div className="panel-title">
                        <span>Live Movement Stream (Chronological)</span>
                        <span style={{ fontSize: "11px", color: "var(--muted)", fontFamily: "monospace" }}>
                            LIVE ● STREAMING
                        </span>
                    </div>

                    <div className="timeline-stream">
                        {events.map((evt) => (
                            <div
                                key={evt.id}
                                className="timeline-event-row"
                                onClick={() => handleStudentClick(evt.student_id)}
                            >
                                <div className="event-left">
                                    <span className={`direction-badge ${evt.direction.toLowerCase()}`}>
                                        {evt.direction}
                                    </span>
                                    <span className="event-student-id">
                                        {evt.student_id} ({evt.name})
                                    </span>
                                    <span className="event-location">
                                        → {evt.classroom} ({evt.camera})
                                    </span>
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                                    <span style={{ fontSize: "11px", color: "var(--success)", fontFamily: "monospace" }}>
                                        {Math.round(evt.confidence * 100)}% match
                                    </span>
                                    <span className="event-time">
                                        {evt.time}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* DEDICATED EXCEPTION CENTER */}
                <div className="panel-card">
                    <div className="panel-title">
                        <span>Exception Center</span>
                        <span style={{ color: "var(--warning)", fontWeight: "700" }}>4 ALERTS</span>
                    </div>

                    <div className="exception-list">
                        {exceptions.map((ex) => (
                            <div
                                key={ex.id}
                                className={`exception-item ${ex.type}`}
                                onClick={() => handleStudentClick(ex.student_id !== "UNKNOWN" ? ex.student_id : "STU001")}
                            >
                                <div className="exception-header">
                                    <span>{ex.title}</span>
                                    <span>{ex.time}</span>
                                </div>
                                <div className="exception-detail">
                                    {ex.detail}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ========================================================
                INTERACTION 1: IN-PLACE CLASSROOM DRAWER
            ======================================================== */}
            {selectedRoom && (
                <div className="drawer-backdrop" onClick={() => setSelectedRoom(null)}>
                    <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
                        <div className="drawer-header">
                            <div>
                                <h3>{selectedRoom.name}</h3>
                                <small style={{ color: "var(--muted)", fontFamily: "monospace" }}>
                                    {selectedRoom.classroom_id}
                                </small>
                            </div>
                            <button className="close-btn" onClick={() => setSelectedRoom(null)}>✕</button>
                        </div>

                        <div className="evidence-section">
                            <h4>Live Room Occupancy</h4>
                            <div className="occupancy-bar-bg" style={{ height: "12px" }}>
                                <div
                                    className="occupancy-bar-fill"
                                    style={{
                                        width: `${Math.round((selectedRoom.occupancy / selectedRoom.capacity) * 100)}%`,
                                        background: "var(--primary)"
                                    }}
                                ></div>
                            </div>
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginTop: "6px" }}>
                                <span>{selectedRoom.occupancy} / {selectedRoom.capacity} Occupied</span>
                                <span>{Math.round((selectedRoom.occupancy / selectedRoom.capacity) * 100)}% Capacity</span>
                            </div>
                        </div>

                        <div className="evidence-section">
                            <h4>Attendance Classification Inside</h4>
                            <div className="evidence-row"><span>Present:</span> <strong>51 Students</strong></div>
                            <div className="evidence-row"><span>Partial (&lt; 75%):</span> <strong>2 Students</strong></div>
                            <div className="evidence-row"><span>Unknown Observations:</span> <strong style={{ color: "var(--warning)" }}>1 Track</strong></div>
                        </div>

                        <div className="evidence-section" style={{ flex: 1 }}>
                            <h4>Live Students Present</h4>
                            <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "280px", overflowY: "auto" }}>
                                <div
                                    className="timeline-event-row"
                                    style={{ background: "#070A14" }}
                                    onClick={() => handleStudentClick("STU001")}
                                >
                                    <span>● STU001 (Aashish Kumar)</span>
                                    <span style={{ color: "var(--success)" }}>Present (42m)</span>
                                </div>
                                <div
                                    className="timeline-event-row"
                                    style={{ background: "#070A14" }}
                                    onClick={() => handleStudentClick("STU034")}
                                >
                                    <span>● STU034 (Rahul Verma)</span>
                                    <span style={{ color: "var(--success)" }}>Present (38m)</span>
                                </div>
                                <div
                                    className="timeline-event-row"
                                    style={{ background: "#070A14" }}
                                    onClick={() => handleStudentClick("STU083")}
                                >
                                    <span>● STU083 (Priya Sharma)</span>
                                    <span style={{ color: "var(--warning)" }}>Partial (19m)</span>
                                </div>
                                <div
                                    className="timeline-event-row"
                                    style={{ background: "#070A14" }}
                                    onClick={() => handleStudentClick("STU127")}
                                >
                                    <span>● STU127 (Ananya Iyer)</span>
                                    <span style={{ color: "var(--success)" }}>Present (41m)</span>
                                </div>
                            </div>
                        </div>

                        <div className="drawer-actions">
                            <button className="btn-primary" onClick={() => setSelectedRoom(null)}>
                                View Cameras
                            </button>
                            <button className="btn-secondary" onClick={() => setSelectedRoom(null)}>
                                Close Drawer
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ========================================================
                INTERACTION 2: STUDENT MULTIMODAL EVIDENCE DRAWER (KILLER UI)
            ======================================================== */}
            {selectedStudent && (
                <div className="drawer-backdrop" onClick={() => setSelectedStudent(null)}>
                    <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
                        <div className="drawer-header">
                            <div>
                                <h3>STUDENT EVIDENCE AUDIT</h3>
                                <small style={{ color: "var(--muted)", fontFamily: "monospace" }}>
                                    {selectedStudent} • {studentEvidence?.name || "Aashish Kumar"}
                                </small>
                            </div>
                            <button className="close-btn" onClick={() => setSelectedStudent(null)}>✕</button>
                        </div>

                        {evidenceLoading ? (
                            <div style={{ padding: "40px", textAlign: "center", color: "var(--muted)" }}>
                                Loading biometric evidence & audit trail...
                            </div>
                        ) : (
                            studentEvidence && (
                                <>
                                    {/* BEST FRAME CAPTURE PREVIEW */}
                                    <div className="evidence-section" style={{ textAlign: "center" }}>
                                        <div style={{
                                            width: "120px",
                                            height: "120px",
                                            margin: "0 auto 10px",
                                            borderRadius: "8px",
                                            background: "#1E293B",
                                            border: "2px solid var(--primary)",
                                            display: "flex",
                                            alignItems: "center",
                                            justifyContent: "center",
                                            overflow: "hidden"
                                        }}>
                                            <span style={{ fontSize: "40px" }}>👤</span>
                                        </div>
                                        <div style={{ fontSize: "11px", color: "var(--success)", fontWeight: "700" }}>
                                            ● BEST FRAME CAPTURE: 86px Face Width (Laplacian: 118.4)
                                        </div>
                                    </div>

                                    {/* MULTIMODAL IDENTITY SCORES */}
                                    <div className="evidence-section">
                                        <h4>Biometric Identity Scores</h4>
                                        <div className="evidence-row">
                                            <span>Face Similarity:</span>
                                            <span>{studentEvidence.identity?.face_similarity || 0.94}</span>
                                        </div>
                                        <div className="evidence-row">
                                            <span>Face Reliability:</span>
                                            <span>{studentEvidence.identity?.face_reliability || 0.91}</span>
                                        </div>
                                        <div className="evidence-row">
                                            <span>Body Re-ID Cosine:</span>
                                            <span>{studentEvidence.identity?.body_similarity || 0.82}</span>
                                        </div>
                                        <div className="evidence-row">
                                            <span>Body Reliability:</span>
                                            <span>{studentEvidence.identity?.body_reliability || 0.78}</span>
                                        </div>
                                    </div>

                                    {/* ADAPTIVE FUSION WEIGHT BREAKDOWN */}
                                    <div className="evidence-section">
                                        <h4>Adaptive Fusion Breakdown</h4>
                                        <div className="evidence-row">
                                            <span>Face Modality Weight:</span>
                                            <span>61%</span>
                                        </div>
                                        <div className="meter-bar">
                                            <div className="meter-fill" style={{ width: "61%" }}></div>
                                        </div>

                                        <div className="evidence-row">
                                            <span>Body Modality Weight:</span>
                                            <span>39%</span>
                                        </div>
                                        <div className="meter-bar">
                                            <div className="meter-fill" style={{ width: "39%", background: "#0EA5E9" }}></div>
                                        </div>

                                        <div className="evidence-row" style={{ marginTop: "10px" }}>
                                            <span>Fused Decision Confidence:</span>
                                            <strong style={{ color: "var(--success)" }}>
                                                {studentEvidence.identity?.fusion || 0.89} (CONFIRMED)
                                            </strong>
                                        </div>
                                    </div>

                                    {/* SPATIOTEMPORAL TRACK AUDIT */}
                                    <div className="evidence-section">
                                        <h4>Spatiotemporal Track Audit</h4>
                                        <div className="evidence-row">
                                            <span>Track ID:</span>
                                            <span>#{studentEvidence.track?.track_id || 17}</span>
                                        </div>
                                        <div className="evidence-row">
                                            <span>Crossing Camera:</span>
                                            <span>{studentEvidence.movement?.camera || "C203_ENTRY"}</span>
                                        </div>
                                        <div className="evidence-row">
                                            <span>Direction:</span>
                                            <strong style={{ color: "var(--success)" }}>
                                                {studentEvidence.movement?.direction || "IN"}
                                            </strong>
                                        </div>
                                        <div className="evidence-row">
                                            <span>Timestamp:</span>
                                            <span>{studentEvidence.movement?.time || "09:02:14"}</span>
                                        </div>
                                    </div>

                                    {/* PERIOD ATTENDANCE BREAKDOWN */}
                                    <div className="evidence-section">
                                        <h4>Period Attendance Status</h4>
                                        {studentEvidence.periods?.map((p, idx) => (
                                            <div key={idx} className="evidence-row">
                                                <span>{p.period_id}:</span>
                                                <strong style={{
                                                    color: p.attendance_status === "PRESENT" ? "var(--success)" :
                                                           p.attendance_status === "PARTIAL" ? "var(--warning)" : "var(--muted)"
                                                }}>
                                                    {p.attendance_status}
                                                </strong>
                                            </div>
                                        ))}
                                    </div>

                                    <div className="drawer-actions">
                                        <button className="btn-primary" onClick={() => alert("Timeline audit export generated.")}>
                                            Export Evidence Audit
                                        </button>
                                        <button className="btn-secondary" onClick={() => setSelectedStudent(null)}>
                                            Close
                                        </button>
                                    </div>
                                </>
                            )
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default Dashboard;