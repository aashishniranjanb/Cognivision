import { useState } from "react";

export default function ClassroomsPage() {
    const [classrooms] = useState([
        { classroom_id: "CLASSROOM_101", name: "Lecture Hall 101", building: "Academic Block A", capacity: 60, occupancy: 58, status: "NORMAL", entryCamera: "C101_ENTRY", exitCamera: "C101_EXIT" },
        { classroom_id: "CLASSROOM_203", name: "VLSI Lab 203", building: "Academic Block B", capacity: 60, occupancy: 54, status: "MISMATCH", difference: 2, entryCamera: "C203_ENTRY", exitCamera: "C203_EXIT" },
        { classroom_id: "CLASSROOM_301", name: "Embedded Systems 301", building: "Academic Block B", capacity: 50, occupancy: 47, status: "NORMAL", entryCamera: "C301_ENTRY", exitCamera: "C301_EXIT" },
        { classroom_id: "CLASSROOM_401", name: "Computer Vision 401", building: "IT & Computing Block", capacity: 65, occupancy: 61, status: "NORMAL", entryCamera: "C401_ENTRY", exitCamera: "C401_EXIT" },
        { classroom_id: "CLASSROOM_501", name: "Seminar Hall 501", building: "Auditorium Complex", capacity: 80, occupancy: 76, status: "NORMAL", entryCamera: "C501_ENTRY", exitCamera: "C501_EXIT" }
    ]);

    const [selectedRoomId, setSelectedRoomId] = useState("CLASSROOM_203");
    const [rosterFilter, setRosterFilter] = useState("ALL");
    const [searchQuery, setSearchQuery] = useState("");
    const [hoveredDot, setHoveredDot] = useState(null);

    const mockStudents = [
        { studentId: "STU001", name: "Aashish Kumar", trackId: 17, status: "PRESENT", duration: "43m 12s", entry: "09:02:14", confidence: 0.94, x: 25, y: 35 },
        { studentId: "STU034", name: "Rahul Verma", trackId: 81, status: "PRESENT", duration: "38m 40s", entry: "09:05:22", confidence: 0.91, x: 45, y: 35 },
        { studentId: "STU083", name: "Priya Sharma", trackId: 19, status: "PARTIAL", duration: "19m 10s", entry: "09:22:15", confidence: 0.89, x: 70, y: 35 },
        { studentId: "STU127", name: "Ananya Iyer", trackId: 54, status: "PRESENT", duration: "41m 05s", entry: "09:03:50", confidence: 0.92, x: 25, y: 65 },
        { studentId: "STU145", name: "Karthik Raj", trackId: 62, status: "PRESENT", duration: "36m 18s", entry: "09:08:12", confidence: 0.95, x: 50, y: 65 },
        { studentId: "STU198", name: "Meera Nair", trackId: 33, status: "PRESENT", duration: "42m 50s", entry: "09:01:45", confidence: 0.93, x: 75, y: 65 },
        { studentId: "UNKNOWN", name: "Unregistered Visitor", trackId: 31, status: "UNKNOWN", duration: "12m 30s", entry: "09:30:10", confidence: 0.38, x: 50, y: 88 }
    ];

    const activeRoom = classrooms.find(r => r.classroom_id === selectedRoomId) || classrooms[0];

    const filteredStudents = mockStudents.filter(s => {
        const matchesFilter = rosterFilter === "ALL" || s.status === rosterFilter;
        const matchesSearch = s.studentId.toLowerCase().includes(searchQuery.toLowerCase()) ||
                              s.name.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    return (
        <div>
            {/* TOPBAR */}
            <div className="topbar">
                <div>
                    <h1>Interactive Classroom Explorer</h1>
                    <p>Spatial Room Floorplan • Live Physical Person Tracking • Discrepancy Audits</p>
                </div>

                <div className="topbar-right">
                    <div className="telemetry-badge">
                        <span>🏢</span>
                        ACTIVE: <strong>{activeRoom.name}</strong>
                    </div>
                    <div className="telemetry-badge">
                        <span>👥</span>
                        OCCUPANCY: <strong style={{ color: "#2563eb" }}>{activeRoom.occupancy} / {activeRoom.capacity}</strong>
                    </div>
                </div>
            </div>

            {/* CLASSROOM SELECTOR STRIP */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "14px", marginBottom: "24px" }}>
                {classrooms.map(c => (
                    <div
                        key={c.classroom_id}
                        className={`room-card ${selectedRoomId === c.classroom_id ? "selected" : ""}`}
                        onClick={() => setSelectedRoomId(c.classroom_id)}
                    >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                            <strong style={{ fontSize: "13px", color: "#172033" }}>{c.name}</strong>
                            <span style={{
                                fontSize: "10px",
                                padding: "2px 6px",
                                borderRadius: "4px",
                                fontWeight: 700,
                                backgroundColor: c.status === "NORMAL" ? "#ecfdf5" : "#fef2f2",
                                color: c.status === "NORMAL" ? "#059669" : "#dc2626"
                            }}>
                                {c.status}
                            </span>
                        </div>
                        <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "8px" }}>{c.building}</div>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#475569" }}>
                            <span>Occupancy:</span>
                            <strong style={{ color: "#0f172a" }}>{c.occupancy} / {c.capacity}</strong>
                        </div>
                    </div>
                ))}
            </div>

            {/* SPATIAL FLOORPLAN & ACTIVE ROSTER */}
            <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: "24px" }}>
                {/* 1. SPATIAL ROOM FLOORPLAN */}
                <div className="panel-card">
                    <div className="panel-title">
                        <span>Spatial Room Map — {activeRoom.name}</span>
                        <span style={{ fontSize: "11px", color: "#16a34a", fontWeight: 600 }}>
                            {activeRoom.occupancy} Persons Detected
                        </span>
                    </div>

                    <div className="floorplan-map">
                        {/* Doorway & Capture Corridor Zone */}
                        <div style={{
                            position: "absolute",
                            bottom: "0",
                            left: "40%",
                            width: "20%",
                            height: "60px",
                            border: "2px dashed #2563eb",
                            background: "rgba(37, 99, 235, 0.08)",
                            borderRadius: "6px 6px 0 0",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "11px",
                            fontWeight: 700,
                            color: "#2563eb"
                        }}>
                            CAPTURE CORRIDOR
                        </div>

                        {/* Instructor Podium */}
                        <div style={{
                            position: "absolute",
                            top: "20px",
                            left: "35%",
                            width: "30%",
                            height: "40px",
                            background: "#e2e8f0",
                            borderRadius: "6px",
                            border: "1px solid #cbd5e1",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontSize: "11px",
                            fontWeight: 600,
                            color: "#475569"
                        }}>
                            PODIUM & PRESENTATION
                        </div>

                        {/* Desks */}
                        {[
                            { x: 15, y: 120 }, { x: 38, y: 120 }, { x: 62, y: 120 }, { x: 80, y: 120 },
                            { x: 15, y: 220 }, { x: 38, y: 220 }, { x: 62, y: 220 }, { x: 80, y: 220 }
                        ].map((d, i) => (
                            <div key={i} className="desk-rect" style={{ left: `${d.x}%`, top: `${d.y}px` }}>
                                Row {Math.floor(i / 4) + 1}
                            </div>
                        ))}

                        {/* Tracked Student Dots (👤) */}
                        {mockStudents.map((st, i) => (
                            <div
                                key={i}
                                className="student-dot"
                                style={{
                                    left: `${st.x}%`,
                                    top: `${st.y}%`,
                                    background: st.status === "PRESENT" ? "#16a34a" : st.status === "PARTIAL" ? "#f59e0b" : "#dc2626"
                                }}
                                onMouseEnter={() => setHoveredDot(st)}
                                onMouseLeave={() => setHoveredDot(null)}
                            >
                                👤
                            </div>
                        ))}

                        {/* Tooltip on dot hover */}
                        {hoveredDot && (
                            <div style={{
                                position: "absolute",
                                left: `${hoveredDot.x}%`,
                                top: `${hoveredDot.y - 12}%`,
                                transform: "translate(-50%, -100%)",
                                background: "#0f172a",
                                color: "#ffffff",
                                padding: "8px 12px",
                                borderRadius: "8px",
                                fontSize: "11px",
                                boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
                                zIndex: 20,
                                whiteSpace: "nowrap"
                            }}>
                                <strong>{hoveredDot.name} ({hoveredDot.studentId})</strong>
                                <div style={{ color: "#38bdf8" }}>Track #{hoveredDot.trackId} • Match: {Math.round(hoveredDot.confidence * 100)}%</div>
                                <div style={{ color: "#94a3b8" }}>Duration: {hoveredDot.duration}</div>
                            </div>
                        )}
                    </div>
                </div>

                {/* 2. CLASSROOM ROSTER TABLE */}
                <div className="panel-card">
                    <div className="panel-title">
                        <span>Students Inside Room</span>
                        <span style={{ fontSize: "11px", color: "#64748b" }}>{filteredStudents.length} Students</span>
                    </div>

                    <div style={{ display: "flex", gap: "8px", marginBottom: "14px" }}>
                        {["ALL", "PRESENT", "PARTIAL", "UNKNOWN"].map(f => (
                            <button
                                key={f}
                                className="btn-secondary"
                                style={{
                                    padding: "4px 10px",
                                    fontSize: "11px",
                                    background: rosterFilter === f ? "#2563eb" : "#ffffff",
                                    color: rosterFilter === f ? "#ffffff" : "#475569",
                                    borderColor: rosterFilter === f ? "#2563eb" : "#cbd5e1"
                                }}
                                onClick={() => setRosterFilter(f)}
                            >
                                {f}
                            </button>
                        ))}
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "330px", overflowY: "auto" }}>
                        {filteredStudents.map((st, i) => (
                            <div key={i} style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                padding: "10px 12px",
                                background: "#f8fafc",
                                border: "1px solid #e2e8f0",
                                borderRadius: "8px"
                            }}>
                                <div>
                                    <strong style={{ fontSize: "13px", color: "#172033" }}>{st.name}</strong>
                                    <div style={{ fontSize: "11px", color: "#64748b" }}>{st.studentId} • Track #{st.trackId}</div>
                                </div>
                                <div style={{ textAlign: "right" }}>
                                    <span style={{
                                        fontSize: "10px",
                                        padding: "2px 6px",
                                        borderRadius: "4px",
                                        fontWeight: 700,
                                        backgroundColor: st.status === "PRESENT" ? "#ecfdf5" : st.status === "PARTIAL" ? "#fffbeb" : "#fef2f2",
                                        color: st.status === "PRESENT" ? "#059669" : st.status === "PARTIAL" ? "#d97706" : "#dc2626"
                                    }}>
                                        {st.status}
                                    </span>
                                    <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "2px" }}>{st.duration}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
