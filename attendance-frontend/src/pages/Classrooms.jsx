import { useState } from "react";

function Classrooms() {
    const [classrooms] = useState([
        {
            classroom_id: "CLASSROOM_101",
            name: "Lecture Hall 101",
            building: "Academic Block A",
            capacity: 60,
            occupancy: 58,
            visionCount: 58,
            status: "NORMAL",
            entryCamera: "C101_ENTRY",
            exitCamera: "C101_EXIT"
        },
        {
            classroom_id: "CLASSROOM_203",
            name: "VLSI Lab 203",
            building: "Academic Block B",
            capacity: 60,
            occupancy: 54,
            visionCount: 54,
            status: "MISMATCH",
            difference: 2,
            entryCamera: "C203_ENTRY",
            exitCamera: "C203_EXIT"
        },
        {
            classroom_id: "CLASSROOM_301",
            name: "Embedded Systems 301",
            building: "Academic Block B",
            capacity: 50,
            occupancy: 47,
            visionCount: 47,
            status: "NORMAL",
            entryCamera: "C301_ENTRY",
            exitCamera: "C301_EXIT"
        },
        {
            classroom_id: "CLASSROOM_401",
            name: "Computer Vision 401",
            building: "IT & Computing Block",
            capacity: 65,
            occupancy: 61,
            visionCount: 61,
            status: "NORMAL",
            entryCamera: "C401_ENTRY",
            exitCamera: "C401_EXIT"
        },
        {
            classroom_id: "CLASSROOM_501",
            name: "Seminar Hall 501",
            building: "Auditorium Complex",
            capacity: 80,
            occupancy: 76,
            visionCount: 76,
            status: "NORMAL",
            entryCamera: "C501_ENTRY",
            exitCamera: "C501_EXIT"
        }
    ]);

    const [selectedRoomId, setSelectedRoomId] = useState("CLASSROOM_203");
    const [rosterFilter, setRosterFilter] = useState("ALL");
    const [searchQuery, setSearchQuery] = useState("");
    const [hoveredDot, setHoveredDot] = useState(null);

    // Mock students inside the active room
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
        <div className="page">
            {/* HEADER */}
            <div className="command-header">
                <div className="command-title">
                    <h1>
                        CLASSROOM EXPLORER
                        <span className="telemetry-badge online">
                            <span className="online-dot"></span>
                            5 ROOMS MONITORED
                        </span>
                    </h1>
                    <div className="command-subtitle">
                        SPATIAL OCCUPANCY MAP & IN-ROOM STUDENT CONTINUITY
                    </div>
                </div>

                <div className="command-telemetry-bar">
                    <div className="telemetry-badge">
                        <span>👥</span>
                        <strong>296 / 315</strong> CAMPUS OCCUPANCY
                    </div>
                    <div className="telemetry-badge">
                        <span>⚡</span>
                        <strong>94.0%</strong> LOAD FACTOR
                    </div>
                </div>
            </div>

            {/* CLASSROOM SELECTOR TABS */}
            <div style={{ display: "flex", gap: "10px", marginBottom: "20px", overflowX: "auto", paddingBottom: "4px" }}>
                {classrooms.map(room => {
                    const isSelected = room.classroom_id === selectedRoomId;
                    const isMismatch = room.status === "MISMATCH";
                    return (
                        <div
                            key={room.classroom_id}
                            style={{
                                background: isSelected ? "rgba(37, 99, 235, 0.2)" : "#0E1526",
                                border: `1px solid ${isSelected ? "var(--primary)" : isMismatch ? "var(--warning)" : "var(--border)"}`,
                                padding: "12px 18px",
                                borderRadius: "8px",
                                cursor: "pointer",
                                minWidth: "180px",
                                transition: "all 0.15s"
                            }}
                            onClick={() => setSelectedRoomId(room.classroom_id)}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "6px" }}>
                                <span style={{ color: "var(--muted)", fontFamily: "monospace" }}>{room.classroom_id}</span>
                                {isMismatch && (
                                    <span style={{ color: "var(--warning)", fontWeight: "700" }}>MISMATCH</span>
                                )}
                            </div>
                            <strong style={{ fontSize: "14px", color: isSelected ? "var(--primary-light)" : "var(--text)", display: "block" }}>
                                {room.name}
                            </strong>
                            <div style={{ fontSize: "12px", color: "var(--muted)", marginTop: "6px" }}>
                                {room.occupancy} / {room.capacity} students ({Math.round(room.occupancy/room.capacity*100)}%)
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* MAIN TWO-COLUMN VIEW */}
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1.8fr", gap: "20px" }}>
                {/* 1. SPATIAL CLASSROOM FLOORPLAN MAP */}
                <div className="panel-card" style={{ background: "#0E1526" }}>
                    <div className="panel-title">
                        <span>Spatial Occupancy Map: {activeRoom.name}</span>
                        <span style={{ fontSize: "11px", color: "var(--primary-light)" }}>
                            {activeRoom.occupancy} TRACKED SUBJECTS
                        </span>
                    </div>

                    {/* SCHEMATIC FLOORPLAN BOX */}
                    <div style={{
                        position: "relative",
                        height: "360px",
                        background: "#080C17",
                        border: "2px dashed var(--border)",
                        borderRadius: "8px",
                        overflow: "hidden"
                    }}>
                        {/* Chalkboard / Front Screen */}
                        <div style={{
                            position: "absolute",
                            top: "8px",
                            left: "20%",
                            right: "20%",
                            height: "14px",
                            background: "#1E293B",
                            border: "1px solid #334155",
                            borderRadius: "4px",
                            textAlign: "center",
                            fontSize: "9px",
                            color: "var(--muted)",
                            letterSpacing: "1px"
                        }}>
                            INSTRUCTOR PODIUM & BOARD
                        </div>

                        {/* Desk Row 1 */}
                        <div style={{ position: "absolute", top: "32%", left: "10%", right: "10%", height: "20px", borderBottom: "1px solid #1E293B" }}></div>
                        {/* Desk Row 2 */}
                        <div style={{ position: "absolute", top: "62%", left: "10%", right: "10%", height: "20px", borderBottom: "1px solid #1E293B" }}></div>

                        {/* Doorway / Capture Zone */}
                        <div style={{
                            position: "absolute",
                            bottom: "0",
                            left: "35%",
                            width: "30%",
                            height: "28px",
                            borderTop: "2px solid var(--success)",
                            background: "rgba(16, 185, 129, 0.08)",
                            textAlign: "center",
                            fontSize: "10px",
                            color: "var(--success)",
                            paddingTop: "6px",
                            fontWeight: "700"
                        }}>
                            🚪 ENTRY / EXIT FUNNEL ({activeRoom.entryCamera})
                        </div>

                        {/* Interactive Tracked Person Dots */}
                        {mockStudents.map((st, i) => (
                            <div
                                key={i}
                                style={{
                                    position: "absolute",
                                    left: `${st.x}%`,
                                    top: `${st.y}%`,
                                    transform: "translate(-50%, -50%)",
                                    cursor: "pointer",
                                    zIndex: 10
                                }}
                                onMouseEnter={() => setHoveredDot(st)}
                                onMouseLeave={() => setHoveredDot(null)}
                            >
                                <div style={{
                                    width: "28px",
                                    height: "28px",
                                    borderRadius: "50%",
                                    background: st.status === "PRESENT" ? "#10B981" : st.status === "PARTIAL" ? "#F59E0B" : "#EF4444",
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    fontSize: "14px",
                                    boxShadow: "0 0 10px rgba(0,0,0,0.8)",
                                    border: hoveredDot?.studentId === st.studentId ? "2px solid #FFF" : "none"
                                }}>
                                    👤
                                </div>
                                <div style={{
                                    position: "absolute",
                                    top: "30px",
                                    left: "50%",
                                    transform: "translateX(-50%)",
                                    fontSize: "9px",
                                    fontFamily: "monospace",
                                    color: "var(--text)",
                                    whiteSpace: "nowrap"
                                }}>
                                    {st.studentId}
                                </div>
                            </div>
                        ))}

                        {/* Hover Information Pill */}
                        {hoveredDot && (
                            <div style={{
                                position: "absolute",
                                top: "12px",
                                right: "12px",
                                background: "rgba(17, 24, 39, 0.95)",
                                border: "1px solid var(--primary)",
                                padding: "8px 12px",
                                borderRadius: "6px",
                                fontSize: "11px",
                                zIndex: 20
                            }}>
                                <div><strong>{hoveredDot.studentId}: {hoveredDot.name}</strong></div>
                                <div style={{ color: "var(--muted)", marginTop: "2px" }}>
                                    Track #{hoveredDot.trackId} • Match {Math.round(hoveredDot.confidence*100)}%
                                </div>
                                <div style={{ color: "var(--success)", marginTop: "2px" }}>
                                    Duration: {hoveredDot.duration}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* RECONCILIATION SUMMARY BOX */}
                    <div style={{ marginTop: "16px", padding: "12px", background: "#090D1A", borderRadius: "6px", border: "1px solid var(--border)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--muted)", marginBottom: "6px" }}>
                            <span>COUNT RECONCILIATION</span>
                            <span style={{ color: activeRoom.status === "MISMATCH" ? "var(--warning)" : "var(--success)" }}>
                                {activeRoom.status === "MISMATCH" ? "⚠️ MINOR MISMATCH (+2)" : "✓ PERFECT MATCH"}
                            </span>
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px", fontSize: "12px", fontFamily: "monospace" }}>
                            <div>Physical Vision: <strong>{activeRoom.visionCount}</strong></div>
                            <div>Event Net Occupancy: <strong>{activeRoom.occupancy}</strong></div>
                            <div>Total Capacity: <strong>{activeRoom.capacity}</strong></div>
                        </div>
                    </div>
                </div>

                {/* 2. IN-ROOM LIVE STUDENT ROSTER TABLE */}
                <div className="panel-card" style={{ background: "#0E1526" }}>
                    <div className="panel-title">
                        <span>Live Student Roster ({filteredStudents.length})</span>
                        <div style={{ display: "flex", gap: "6px" }}>
                            {["ALL", "PRESENT", "PARTIAL", "UNKNOWN"].map(f => (
                                <button
                                    key={f}
                                    style={{
                                        background: rosterFilter === f ? "var(--primary)" : "#1E293B",
                                        border: "none",
                                        color: "#FFF",
                                        fontSize: "10px",
                                        fontWeight: "700",
                                        padding: "4px 8px",
                                        borderRadius: "4px",
                                        cursor: "pointer"
                                    }}
                                    onClick={() => setRosterFilter(f)}
                                >
                                    {f}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Search filter input */}
                    <div style={{ marginBottom: "12px" }}>
                        <input
                            type="text"
                            placeholder="Search Student ID or Name..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{
                                width: "100%",
                                padding: "8px 12px",
                                background: "#090D1A",
                                border: "1px solid var(--border)",
                                borderRadius: "6px",
                                color: "var(--text)",
                                fontSize: "12px"
                            }}
                        />
                    </div>

                    {/* Table */}
                    <div style={{ maxHeight: "360px", overflowY: "auto" }}>
                        <table>
                            <thead>
                                <tr>
                                    <th>Student</th>
                                    <th>Track</th>
                                    <th>Entry</th>
                                    <th>Duration</th>
                                    <th>Status</th>
                                    <th>Match</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredStudents.map((st, i) => (
                                    <tr key={i} style={{ cursor: "pointer" }}>
                                        <td>
                                            <strong style={{ color: "var(--primary-light)" }}>{st.studentId}</strong>
                                            <div style={{ fontSize: "11px", color: "var(--muted)" }}>{st.name}</div>
                                        </td>
                                        <td style={{ fontFamily: "monospace" }}>#{st.trackId}</td>
                                        <td style={{ fontFamily: "monospace", fontSize: "11px" }}>{st.entry}</td>
                                        <td style={{ fontFamily: "monospace", color: "var(--success)" }}>{st.duration}</td>
                                        <td>
                                            <span style={{
                                                fontSize: "10px",
                                                padding: "2px 6px",
                                                borderRadius: "4px",
                                                fontWeight: "700",
                                                background: st.status === "PRESENT" ? "rgba(16,185,129,0.15)" : st.status === "PARTIAL" ? "rgba(245,158,11,0.15)" : "rgba(239,68,68,0.15)",
                                                color: st.status === "PRESENT" ? "var(--success)" : st.status === "PARTIAL" ? "var(--warning)" : "var(--danger)"
                                            }}>
                                                {st.status}
                                            </span>
                                        </td>
                                        <td style={{ fontFamily: "monospace", color: "var(--success)" }}>
                                            {Math.round(st.confidence * 100)}%
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Classrooms;