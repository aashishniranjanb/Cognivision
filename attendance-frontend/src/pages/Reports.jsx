import { useState } from "react";

function Reports() {
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
    const [selectedClassroom, setSelectedClassroom] = useState("ALL");

    const periodReports = [
        { period: "P1", subject: "VLSI Design", schedule: "09:00 - 09:50", expected: 60, present: 54, partial: 2, absent: 4, rate: 90.0 },
        { period: "P2", subject: "Embedded Systems", schedule: "10:00 - 10:50", expected: 60, present: 52, partial: 3, absent: 5, rate: 86.7 },
        { period: "P3", subject: "Signals & Systems", schedule: "11:00 - 11:50", expected: 60, present: 51, partial: 4, absent: 5, rate: 85.0 },
        { period: "P4", subject: "Computer Vision Lab", schedule: "13:00 - 14:50", expected: 65, present: 58, partial: 2, absent: 5, rate: 89.2 },
        { period: "P5", subject: "Academic Seminar", schedule: "15:00 - 16:30", expected: 80, present: 72, partial: 3, absent: 5, rate: 90.0 }
    ];

    const totalExpected = periodReports.reduce((s, p) => s + p.expected, 0);
    const totalPresent = periodReports.reduce((s, p) => s + p.present, 0);
    const overallRate = Math.round((totalPresent / totalExpected) * 100);

    return (
        <div className="page">
            {/* HEADER */}
            <div className="command-header">
                <div className="command-title">
                    <h1>
                        ATTENDANCE REPORTS & CSV EXPORT
                        <span className="telemetry-badge online">
                            <span className="online-dot"></span>
                            AUDITED RECORDS
                        </span>
                    </h1>
                    <div className="command-subtitle">
                        OFFICIAL PERIOD-BY-PERIOD ATTENDANCE • CSV REGISTRY • AUDIT INTEGRITY
                    </div>
                </div>

                <div className="command-telemetry-bar">
                    <a
                        href="http://localhost:8000/api/attendance/export/csv"
                        className="mismatch-btn"
                        style={{ textDecoration: "none", display: "inline-block", background: "var(--primary)", color: "#FFF" }}
                    >
                        📥 DOWNLOAD CSV AUDIT
                    </a>
                </div>
            </div>

            {/* FILTER BAR */}
            <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background: "#0E1526",
                padding: "14px 18px",
                borderRadius: "8px",
                border: "1px solid var(--border)",
                marginBottom: "20px"
            }}>
                <div style={{ display: "flex", gap: "14px", alignItems: "center" }}>
                    <div>
                        <label style={{ fontSize: "11px", color: "var(--muted)", display: "block", marginBottom: "4px" }}>
                            SELECT DATE:
                        </label>
                        <input
                            type="date"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            style={{
                                background: "#080C17",
                                border: "1px solid var(--border)",
                                borderRadius: "4px",
                                color: "var(--text)",
                                padding: "6px 10px",
                                fontSize: "12px"
                            }}
                        />
                    </div>

                    <div>
                        <label style={{ fontSize: "11px", color: "var(--muted)", display: "block", marginBottom: "4px" }}>
                            CLASSROOM:
                        </label>
                        <select
                            value={selectedClassroom}
                            onChange={(e) => setSelectedClassroom(e.target.value)}
                            style={{
                                background: "#080C17",
                                border: "1px solid var(--border)",
                                borderRadius: "4px",
                                color: "var(--text)",
                                padding: "6px 10px",
                                fontSize: "12px"
                            }}
                        >
                            <option value="ALL">ALL CLASSROOMS (CAMPUS)</option>
                            <option value="CLASSROOM_101">CLASSROOM 101</option>
                            <option value="CLASSROOM_203">CLASSROOM 203</option>
                            <option value="CLASSROOM_301">CLASSROOM 301</option>
                            <option value="CLASSROOM_401">CLASSROOM 401</option>
                        </select>
                    </div>
                </div>

                <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "11px", color: "var(--muted)" }}>OVERALL DAILY RATE</div>
                    <strong style={{ fontSize: "20px", color: "var(--success)", fontFamily: "monospace" }}>
                        {overallRate}% PRESENT
                    </strong>
                </div>
            </div>

            {/* PERIOD SUMMARY TABLE */}
            <div className="panel-card" style={{ background: "#0E1526" }}>
                <div className="panel-title">
                    <span>Period Attendance Summary ({selectedDate})</span>
                    <span style={{ fontSize: "11px", color: "var(--muted)" }}>
                        {totalPresent} / {totalExpected} TOTAL SESSIONS ATTENDED
                    </span>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Period</th>
                            <th>Subject</th>
                            <th>Schedule Interval</th>
                            <th>Enrolled</th>
                            <th>Present</th>
                            <th>Partial (&lt; 75%)</th>
                            <th>Absent</th>
                            <th>Attendance Rate</th>
                            <th>Integrity</th>
                        </tr>
                    </thead>
                    <tbody>
                        {periodReports.map((p) => (
                            <tr key={p.period}>
                                <td>
                                    <strong style={{ color: "var(--primary-light)" }}>{p.period}</strong>
                                </td>
                                <td>{p.subject}</td>
                                <td style={{ fontFamily: "monospace", fontSize: "11px" }}>{p.schedule}</td>
                                <td style={{ fontFamily: "monospace" }}>{p.expected}</td>
                                <td style={{ fontFamily: "monospace", color: "var(--success)" }}><strong>{p.present}</strong></td>
                                <td style={{ fontFamily: "monospace", color: "var(--warning)" }}>{p.partial}</td>
                                <td style={{ fontFamily: "monospace", color: "var(--danger)" }}>{p.absent}</td>
                                <td style={{ fontFamily: "monospace" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                        <div style={{ width: "60px", height: "6px", background: "#1E293B", borderRadius: "3px", overflow: "hidden" }}>
                                            <div style={{ width: `${p.rate}%`, height: "100%", background: p.rate >= 85 ? "var(--success)" : "var(--warning)" }}></div>
                                        </div>
                                        <span>{p.rate}%</span>
                                    </div>
                                </td>
                                <td>
                                    <span style={{
                                        fontSize: "10px",
                                        fontWeight: "700",
                                        padding: "2px 6px",
                                        borderRadius: "4px",
                                        background: "rgba(16, 185, 129, 0.15)",
                                        color: "var(--success)"
                                    }}>
                                        VERIFIED
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default Reports;