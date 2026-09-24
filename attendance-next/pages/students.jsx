import { useState } from "react";
import { getStudentEvidence } from "../services/api";

export default function StudentsPage() {
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
        <div>
            {/* TOPBAR */}
            <div className="topbar">
                <div>
                    <h1>Student Investigation Console</h1>
                    <p>Multimodal Biometric Audit Trail • Explainable Identity Fusion • Forensic Record Drawer</p>
                </div>

                <div className="topbar-right">
                    <div className="telemetry-badge">
                        <span>👥</span>
                        <strong>500</strong> ENROLLED
                    </div>
                    <div className="telemetry-badge">
                        <span>✓</span>
                        <strong style={{ color: "#16a34a" }}>296</strong> PRESENT TODAY
                    </div>
                </div>
            </div>

            {/* FILTER & SEARCH */}
            <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "20px",
                gap: "16px"
            }}>
                <div style={{ display: "flex", gap: "8px" }}>
                    {["ALL", "PRESENT", "PARTIAL", "ABSENT", "UNCERTAIN"].map(st => (
                        <button
                            key={st}
                            className={`mode-toggle-btn ${statusFilter === st ? "active" : ""}`}
                            style={{
                                background: statusFilter === st ? "#2563eb" : "#ffffff",
                                color: statusFilter === st ? "#ffffff" : "#475569",
                                borderColor: statusFilter === st ? "#2563eb" : "#cbd5e1"
                            }}
                            onClick={() => setStatusFilter(st)}
                        >
                            {st}
                        </button>
                    ))}
                </div>

                <input
                    type="text"
                    placeholder="Search by student ID, name, or department..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{
                        padding: "9px 16px",
                        borderRadius: "8px",
                        border: "1px solid #cbd5e1",
                        background: "#ffffff",
                        color: "#172033",
                        fontSize: "13px",
                        width: "320px",
                        outline: "none"
                    }}
                />
            </div>

            {/* STUDENTS TABLE */}
            <div className="panel-card" style={{ padding: "0", overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
                    <thead>
                        <tr style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0", color: "#64748b" }}>
                            <th style={{ padding: "14px 20px" }}>STUDENT</th>
                            <th style={{ padding: "14px 16px" }}>DEPT / YEAR</th>
                            <th style={{ padding: "14px 16px" }}>LOCATION</th>
                            <th style={{ padding: "14px 16px" }}>STATUS</th>
                            <th style={{ padding: "14px 16px" }}>DURATION</th>
                            <th style={{ padding: "14px 16px" }}>FACE SIM</th>
                            <th style={{ padding: "14px 16px" }}>BODY SIM</th>
                            <th style={{ padding: "14px 20px", textAlign: "right" }}>ACTIONS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map((s, idx) => (
                            <tr key={idx} style={{ borderBottom: "1px solid #f1f5f9", transition: "background 0.2s" }}
                                onMouseEnter={(e) => e.currentTarget.style.background = "#f8fafc"}
                                onMouseLeave={(e) => e.currentTarget.style.background = "#ffffff"}
                            >
                                <td style={{ padding: "14px 20px" }}>
                                    <strong style={{ color: "#172033" }}>{s.name}</strong>
                                    <div style={{ fontSize: "11px", color: "#64748b" }}>{s.studentId}</div>
                                </td>
                                <td style={{ padding: "14px 16px", color: "#475569" }}>
                                    {s.department} • Year {s.year}
                                </td>
                                <td style={{ padding: "14px 16px", color: "#475569" }}>
                                    {s.location}
                                </td>
                                <td style={{ padding: "14px 16px" }}>
                                    <span style={{
                                        fontSize: "11px",
                                        padding: "3px 8px",
                                        borderRadius: "6px",
                                        fontWeight: 700,
                                        backgroundColor: s.status === "PRESENT" ? "#ecfdf5" : s.status === "PARTIAL" ? "#fffbeb" : s.status === "UNCERTAIN" ? "#fef2f2" : "#f1f5f9",
                                        color: s.status === "PRESENT" ? "#059669" : s.status === "PARTIAL" ? "#d97706" : s.status === "UNCERTAIN" ? "#dc2626" : "#64748b"
                                    }}>
                                        {s.status}
                                    </span>
                                </td>
                                <td style={{ padding: "14px 16px", color: "#172033", fontWeight: 600 }}>
                                    {s.duration}
                                </td>
                                <td style={{ padding: "14px 16px", color: s.faceConfidence >= 0.8 ? "#16a34a" : "#dc2626", fontWeight: 700 }}>
                                    {s.faceConfidence > 0 ? `${Math.round(s.faceConfidence * 100)}%` : "N/A"}
                                </td>
                                <td style={{ padding: "14px 16px", color: s.bodyScore >= 0.8 ? "#2563eb" : "#d97706", fontWeight: 700 }}>
                                    {s.bodyScore > 0 ? `${Math.round(s.bodyScore * 100)}%` : "N/A"}
                                </td>
                                <td style={{ padding: "14px 20px", textAlign: "right" }}>
                                    <button
                                        className="btn-primary"
                                        style={{ padding: "5px 12px", fontSize: "11px" }}
                                        onClick={() => handleInspect(s)}
                                    >
                                        Inspect Evidence
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* FORENSIC EVIDENCE DRAWER */}
            {selectedStudent && (
                <div className="drawer-overlay" onClick={() => setSelectedStudent(null)}>
                    <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
                        <div className="evidence-header">
                            <div>
                                <h3 style={{ margin: 0, color: "#172033", fontSize: "18px" }}>Biometric Evidence Audit</h3>
                                <div style={{ fontSize: "12px", color: "#64748b" }}>Student ID: {selectedStudent}</div>
                            </div>
                            <button className="btn-secondary" onClick={() => setSelectedStudent(null)}>✕</button>
                        </div>

                        {loadingEvidence ? (
                            <div style={{ textAlign: "center", padding: "40px", color: "#64748b" }}>Loading multi-modal evidence...</div>
                        ) : (
                            evidenceData && (
                                <>
                                    <div className="evidence-crop">
                                        <div style={{ textAlign: "center", color: "#94a3b8" }}>
                                            <div style={{ fontSize: "40px", marginBottom: "8px" }}>👤</div>
                                            <div style={{ color: "#f8fafc", fontWeight: 600 }}>Best Frame Crop: Track #{evidenceData.track?.track_id}</div>
                                            <div style={{ fontSize: "11px", color: "#64748b" }}>Face Width: 104px • Laplacian: 148.2</div>
                                        </div>
                                    </div>

                                    <div className="evidence-section">
                                        <h4>Biometric Multimodal Scores</h4>
                                        <div className="evidence-row">
                                            <span>ArcFace Facial Similarity:</span>
                                            <strong style={{ color: "#16a34a" }}>{evidenceData.identity?.face_similarity} (Reliability: {evidenceData.identity?.face_reliability})</strong>
                                        </div>
                                        <div className="evidence-row">
                                            <span>OSNet Body Appearance:</span>
                                            <strong style={{ color: "#2563eb" }}>{evidenceData.identity?.body_similarity} (Reliability: {evidenceData.identity?.body_reliability})</strong>
                                        </div>
                                        <div className="evidence-row">
                                            <span>Adaptive Fusion Composite:</span>
                                            <strong style={{ color: "#0f172a" }}>{evidenceData.identity?.fusion} ({evidenceData.identity?.decision})</strong>
                                        </div>
                                    </div>

                                    <div className="evidence-section">
                                        <h4>Transit Corridor Telemetry</h4>
                                        <div className="evidence-row"><span>Camera:</span> <strong>{evidenceData.movement?.camera}</strong></div>
                                        <div className="evidence-row"><span>Direction:</span> <strong>{evidenceData.movement?.direction}</strong></div>
                                        <div className="evidence-row"><span>Time:</span> <strong>{evidenceData.movement?.time}</strong></div>
                                    </div>

                                    <div className="evidence-section">
                                        <h4>Period Attendance Status</h4>
                                        {evidenceData.periods?.map((p, i) => (
                                            <div key={i} className="evidence-row">
                                                <span>{p.period_id}:</span>
                                                <strong style={{
                                                    color: p.attendance_status === "PRESENT" ? "#16a34a" : p.attendance_status === "PARTIAL" ? "#d97706" : "#64748b"
                                                }}>
                                                    {p.attendance_status}
                                                </strong>
                                            </div>
                                        ))}
                                    </div>

                                    <div style={{ display: "flex", gap: "10px", marginTop: "auto" }}>
                                        <button className="btn-primary" style={{ flex: 1 }} onClick={() => alert("Audit file generated.")}>
                                            Export Case File
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
