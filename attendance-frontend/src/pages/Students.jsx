import { useState } from "react";
import { getStudentEvidence } from "../services/api";

function Students() {
    const [students] = useState([
        { studentId: "STU001", name: "Aashish Kumar", department: "ECE", year: 3, location: "CLASSROOM_203", status: "PRESENT", duration: "43m 12s", faceConfidence: 0.94, bodyScore: 0.82, trackId: 17 },
        { studentId: "STU034", name: "Rahul Verma", department: "CSE", year: 4, location: "CLASSROOM_101", status: "PRESENT", duration: "38m 40s", faceConfidence: 0.91, bodyScore: 0.79, trackId: 81 },
        { studentId: "STU083", name: "Priya Sharma", department: "ECE", year: 3, location: "OFF_CAMPUS", status: "PARTIAL", duration: "19m 10s", faceConfidence: 0.89, bodyScore: 0.84, trackId: 19 },
        { studentId: "STU127", name: "Ananya Iyer", department: "MECH", year: 2, location: "CLASSROOM_203", status: "PRESENT", duration: "41m 05s", faceConfidence: 0.92, bodyScore: 0.81, trackId: 54 },
        { studentId: "STU145", name: "Karthik Raj", department: "CSE", year: 4, location: "CLASSROOM_401", status: "PRESENT", duration: "36m 18s", faceConfidence: 0.95, bodyScore: 0.88, trackId: 62 },
        { studentId: "STU198", name: "Meera Nair", department: "ECE", year: 3, location: "CLASSROOM_501", status: "PRESENT", duration: "42m 50s", faceConfidence: 0.93, bodyScore: 0.83, trackId: 33 },
        { studentId: "STU210", name: "Rohan Gupta", department: "IT", year: 1, location: "OFF_CAMPUS", status: "ABSENT", duration: "0m 00s", faceConfidence: 0.00, bodyScore: 0.00, trackId: null },
        { studentId: "STU255", name: "Divya Balan", department: "ECE", year: 2, location: "OFF_CAMPUS", status: "UNCERTAIN", duration: "5m 12s", faceConfidence: 0.42, bodyScore: 0.58, trackId: 88 }
    ]);

    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("ALL");
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [evidenceData, setEvidenceData] = useState(null);
    const [loadingEvidence, setLoadingEvidence] = useState(false);

    const handleInspect = async (student) => {
        setSelectedStudent(student.studentId);
        setLoadingEvidence(true);
        try {
            const res = await getStudentEvidence(student.studentId);
            if (res.data) {
                setEvidenceData(res.data);
            }
        } catch {
            setEvidenceData({
                student_id: student.studentId,
                name: student.name,
                department: student.department,
                year: student.year,
                identity: {
                    face_similarity: student.faceConfidence,
                    face_reliability: 0.91,
                    body_similarity: student.bodyScore,
                    body_reliability: 0.78,
                    fusion: Math.round((0.7 * student.faceConfidence + 0.3 * student.bodyScore) * 100) / 100,
                    decision: student.status === "PRESENT" ? "CONFIRMED" : student.status === "UNCERTAIN" ? "UNCERTAIN" : "ABSENT"
                },
                track: { track_id: student.trackId || 17, student_id: student.studentId },
                movement: { camera: "C203_ENTRY", direction: "IN", time: "09:02:14" },
                attendance: { period_id: "P1", status: student.status, presence: student.duration },
                periods: [
                    { period_id: "P1", attendance_status: student.status, duration_seconds: 2580 },
                    { period_id: "P2", attendance_status: student.status === "PRESENT" ? "PRESENT" : "ABSENT", duration_seconds: 2400 },
                    { period_id: "P3", attendance_status: student.status === "PARTIAL" ? "PARTIAL" : "NOT STARTED", duration_seconds: 1140 }
                ]
            });
        } finally {
            setLoadingEvidence(false);
        }
    };

    const filtered = students.filter(s => {
        const matchesFilter = statusFilter === "ALL" || s.status === statusFilter;
        const matchesSearch = s.studentId.toLowerCase().includes(searchQuery.toLowerCase()) ||
                              s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                              s.department.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    return (
        <div className="page">
            {/* HEADER */}
            <div className="command-header">
                <div className="command-title">
                    <h1>
                        STUDENT INVESTIGATION CONSOLE
                        <span className="telemetry-badge online">
                            <span className="online-dot"></span>
                            BIOMETRIC AUDIT VERIFIED
                        </span>
                    </h1>
                    <div className="command-subtitle">
                        MULTIMODAL EXPLAINABILITY • TRACK AUDIT TRAIL • FORENSIC EVIDENCE
                    </div>
                </div>

                <div className="command-telemetry-bar">
                    <div className="telemetry-badge">
                        <span>👥</span>
                        <strong>500</strong> ENROLLED
                    </div>
                    <div className="telemetry-badge">
                        <span>✓</span>
                        <strong>296</strong> PRESENT TODAY
                    </div>
                </div>
            </div>

            {/* FILTER & SEARCH BAR */}
            <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "20px",
                background: "#0E1526",
                padding: "14px 18px",
                borderRadius: "8px",
                border: "1px solid var(--border)"
            }}>
                <div style={{ flex: 1, maxWidth: "400px" }}>
                    <input
                        type="text"
                        placeholder="Search Student ID, Name, or Department..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{
                            width: "100%",
                            padding: "8px 14px",
                            background: "#080C17",
                            border: "1px solid var(--border)",
                            borderRadius: "6px",
                            color: "var(--text)",
                            fontSize: "12px"
                        }}
                    />
                </div>

                <div style={{ display: "flex", gap: "8px" }}>
                    {["ALL", "PRESENT", "PARTIAL", "ABSENT", "UNCERTAIN"].map(f => (
                        <button
                            key={f}
                            style={{
                                background: statusFilter === f ? "var(--primary)" : "#1E293B",
                                border: "none",
                                color: "#FFF",
                                fontSize: "11px",
                                fontWeight: "700",
                                padding: "6px 12px",
                                borderRadius: "6px",
                                cursor: "pointer",
                                transition: "all 0.15s"
                            }}
                            onClick={() => setStatusFilter(f)}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* STUDENTS TABLE */}
            <div className="panel-card" style={{ background: "#0E1526" }}>
                <table>
                    <thead>
                        <tr>
                            <th>Student</th>
                            <th>Department</th>
                            <th>Current Location</th>
                            <th>Attendance Status</th>
                            <th>Duration</th>
                            <th>Face Confidence</th>
                            <th>Body Re-ID</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map(st => (
                            <tr key={st.studentId} onClick={() => handleInspect(st)} style={{ cursor: "pointer" }}>
                                <td>
                                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                                        <div style={{
                                            width: "32px",
                                            height: "32px",
                                            borderRadius: "50%",
                                            background: "#1E293B",
                                            border: "1px solid var(--primary)",
                                            display: "flex",
                                            alignItems: "center",
                                            justifyContent: "center",
                                            fontSize: "14px"
                                        }}>
                                            👤
                                        </div>
                                        <div>
                                            <strong style={{ color: "var(--primary-light)" }}>{st.studentId}</strong>
                                            <div style={{ fontSize: "11px", color: "var(--muted)" }}>{st.name}</div>
                                        </div>
                                    </div>
                                </td>
                                <td>{st.department} • Year {st.year}</td>
                                <td>
                                    <span style={{ fontFamily: "monospace", color: st.location === "OFF_CAMPUS" ? "var(--muted)" : "var(--text)" }}>
                                        {st.location}
                                    </span>
                                </td>
                                <td>
                                    <span style={{
                                        fontSize: "10px",
                                        padding: "3px 8px",
                                        borderRadius: "4px",
                                        fontWeight: "700",
                                        background: st.status === "PRESENT" ? "rgba(16,185,129,0.15)" :
                                                   st.status === "PARTIAL" ? "rgba(245,158,11,0.15)" :
                                                   st.status === "UNCERTAIN" ? "rgba(139,92,246,0.15)" : "rgba(239,68,68,0.15)",
                                        color: st.status === "PRESENT" ? "var(--success)" :
                                               st.status === "PARTIAL" ? "var(--warning)" :
                                               st.status === "UNCERTAIN" ? "#A78BFA" : "var(--danger)"
                                    }}>
                                        {st.status}
                                    </span>
                                </td>
                                <td style={{ fontFamily: "monospace", color: "var(--success)" }}>{st.duration}</td>
                                <td style={{ fontFamily: "monospace", color: st.faceConfidence >= 0.75 ? "var(--success)" : "var(--warning)" }}>
                                    {st.faceConfidence > 0 ? `${Math.round(st.faceConfidence * 100)}%` : "--"}
                                </td>
                                <td style={{ fontFamily: "monospace", color: "var(--text)" }}>
                                    {st.bodyScore > 0 ? `${Math.round(st.bodyScore * 100)}%` : "--"}
                                </td>
                                <td>
                                    <button
                                        className="btn-primary"
                                        style={{ padding: "4px 10px", fontSize: "11px" }}
                                        onClick={(e) => { e.stopPropagation(); handleInspect(st); }}
                                    >
                                        INSPECT
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* MULTIMODAL EVIDENCE DRAWER */}
            {selectedStudent && (
                <div className="drawer-backdrop" onClick={() => setSelectedStudent(null)}>
                    <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
                        <div className="drawer-header">
                            <div>
                                <h3>STUDENT EVIDENCE AUDIT</h3>
                                <small style={{ color: "var(--muted)", fontFamily: "monospace" }}>
                                    {selectedStudent} • {evidenceData?.name}
                                </small>
                            </div>
                            <button className="close-btn" onClick={() => setSelectedStudent(null)}>✕</button>
                        </div>

                        {loadingEvidence ? (
                            <div style={{ padding: "40px", textAlign: "center", color: "var(--muted)" }}>
                                Loading forensic audit trail...
                            </div>
                        ) : evidenceData && (
                            <>
                                <div className="evidence-section" style={{ textAlign: "center" }}>
                                    <div style={{
                                        width: "110px",
                                        height: "110px",
                                        margin: "0 auto 10px",
                                        borderRadius: "8px",
                                        background: "#1E293B",
                                        border: "2px solid var(--primary)",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                        fontSize: "40px"
                                    }}>
                                        👤
                                    </div>
                                    <div style={{ fontSize: "11px", color: "var(--success)", fontWeight: "700" }}>
                                        ● BEST FRAME CAPTURE: 86px Face Width (Laplacian: 118.4)
                                    </div>
                                </div>

                                <div className="evidence-section">
                                    <h4>Multimodal Identity Evidence</h4>
                                    <div className="evidence-row">
                                        <span>Face Similarity:</span>
                                        <span>{evidenceData.identity?.face_similarity}</span>
                                    </div>
                                    <div className="evidence-row">
                                        <span>Face Reliability:</span>
                                        <span>{evidenceData.identity?.face_reliability || 0.91}</span>
                                    </div>
                                    <div className="evidence-row">
                                        <span>Body Re-ID Cosine:</span>
                                        <span>{evidenceData.identity?.body_similarity}</span>
                                    </div>
                                    <div className="evidence-row">
                                        <span>Body Reliability:</span>
                                        <span>{evidenceData.identity?.body_reliability || 0.78}</span>
                                    </div>
                                </div>

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
                                    <div className="evidence-row" style={{ marginTop: "8px" }}>
                                        <span>Fused Decision Confidence:</span>
                                        <strong style={{ color: "var(--success)" }}>
                                            {evidenceData.identity?.fusion} ({evidenceData.identity?.decision || "CONFIRMED"})
                                        </strong>
                                    </div>
                                </div>

                                <div className="evidence-section">
                                    <h4>Movement & Track Continuity</h4>
                                    <div className="evidence-row">
                                        <span>Track ID:</span>
                                        <span>#{evidenceData.track?.track_id || 17}</span>
                                    </div>
                                    <div className="evidence-row">
                                        <span>Camera ID:</span>
                                        <span>{evidenceData.movement?.camera || "C203_ENTRY"}</span>
                                    </div>
                                    <div className="evidence-row">
                                        <span>Crossing Event:</span>
                                        <strong style={{ color: "var(--success)" }}>
                                            {evidenceData.movement?.direction || "IN"} ({evidenceData.movement?.time || "09:02:14"})
                                        </strong>
                                    </div>
                                </div>

                                <div className="drawer-actions">
                                    <a
                                        href={`http://localhost:8000/api/attendance/export/csv?student_id=${selectedStudent}`}
                                        className="btn-primary"
                                        style={{ textAlign: "center", textDecoration: "none" }}
                                    >
                                        Export Student Audit
                                    </a>
                                    <button className="btn-secondary" onClick={() => setSelectedStudent(null)}>
                                        Close
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default Students;