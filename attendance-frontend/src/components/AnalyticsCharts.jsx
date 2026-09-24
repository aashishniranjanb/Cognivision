import { useState } from "react";

export default function AnalyticsCharts() {
    const [hoveredPeriod, setHoveredPeriod] = useState(null);

    // Period attendance trend data (P1..P5)
    const periodData = [
        { period: "P1", subject: "VLSI Design", rate: 94, present: 294, time: "09:00" },
        { period: "P2", subject: "Embedded Sys", rate: 91, present: 285, time: "10:00" },
        { period: "P3", subject: "Signals & Sys", rate: 86, present: 268, time: "11:00" },
        { period: "P4", subject: "CV Lab", rate: 82, present: 256, time: "13:00" },
        { period: "P5", subject: "Core Seminar", rate: 89, present: 278, time: "14:00" }
    ];

    // Compute SVG path coordinates (width 500, height 120, padding 20)
    const svgWidth = 500;
    const svgHeight = 120;
    const padX = 40;
    const padY = 20;

    const points = periodData.map((d, i) => {
        const x = padX + (i * (svgWidth - 2 * padX)) / (periodData.length - 1);
        // Normalize 70% - 100% to Y axis
        const norm = (d.rate - 70) / 30;
        const y = svgHeight - padY - norm * (svgHeight - 2 * padY);
        return { ...d, x, y };
    });

    const pathD = points.reduce((acc, pt, i) => {
        return i === 0 ? `M ${pt.x},${pt.y}` : `${acc} L ${pt.x},${pt.y}`;
    }, "");

    const areaD = `${pathD} L ${points[points.length - 1].x},${svgHeight - padY} L ${points[0].x},${svgHeight - padY} Z`;

    // FPS jitter data points (last 10 seconds)
    const fpsPoints = [24.8, 25.1, 24.9, 25.2, 25.0, 25.3, 25.1, 24.9, 25.2, 25.1];
    const fpsSvgWidth = 240;
    const fpsSvgHeight = 50;
    const fpsPointsCoords = fpsPoints.map((fps, i) => {
        const x = (i * fpsSvgWidth) / (fpsPoints.length - 1);
        const y = fpsSvgHeight - ((fps - 24.0) / 2.0) * fpsSvgHeight;
        return `${x},${y}`;
    }).join(" ");

    return (
        <div className="analytics-section" style={{ marginTop: "24px" }}>
            <div style={{
                display: "grid",
                gridTemplateColumns: "1.4fr 1fr",
                gap: "20px"
            }}>
                {/* 1. PERIOD ATTENDANCE TREND CHART */}
                <div className="panel-card" style={{ background: "#0E1526" }}>
                    <div className="panel-title">
                        <span>Period Attendance Trend (P1 → P5)</span>
                        <span style={{ fontSize: "11px", color: "var(--success)" }}>
                            Average 88.4% Attendance
                        </span>
                    </div>

                    <div style={{ position: "relative" }}>
                        <svg
                            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                            style={{ width: "100%", height: "130px", overflow: "visible" }}
                        >
                            <defs>
                                <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#2563EB" stopOpacity="0.4" />
                                    <stop offset="100%" stopColor="#2563EB" stopOpacity="0.0" />
                                </linearGradient>
                            </defs>

                            {/* Horizontal guide lines */}
                            <line x1={padX} y1={padY} x2={svgWidth - padX} y2={padY} stroke="#1E293B" strokeDasharray="3 3" />
                            <line x1={padX} y1={svgHeight / 2} x2={svgWidth - padX} y2={svgHeight / 2} stroke="#1E293B" strokeDasharray="3 3" />
                            <line x1={padX} y1={svgHeight - padY} x2={svgWidth - padX} y2={svgHeight - padY} stroke="#1E293B" />

                            {/* Shaded Area */}
                            <path d={areaD} fill="url(#trendGradient)" />

                            {/* Curve Line */}
                            <path d={pathD} fill="none" stroke="#3B82F6" strokeWidth="2.5" strokeLinecap="round" />

                            {/* Data Points */}
                            {points.map((pt, i) => (
                                <g key={i}>
                                    <circle
                                        cx={pt.x}
                                        cy={pt.y}
                                        r={hoveredPeriod?.period === pt.period ? 6 : 4}
                                        fill={hoveredPeriod?.period === pt.period ? "#FFF" : "#3B82F6"}
                                        stroke="#1E40AF"
                                        strokeWidth="2"
                                        style={{ cursor: "pointer", transition: "all 0.2s" }}
                                        onMouseEnter={() => setHoveredPeriod(pt)}
                                        onMouseLeave={() => setHoveredPeriod(null)}
                                    />
                                    <text
                                        x={pt.x}
                                        y={svgHeight - 4}
                                        textAnchor="middle"
                                        fill="#94A3B8"
                                        fontSize="10"
                                        fontFamily="monospace"
                                    >
                                        {pt.period}
                                    </text>
                                </g>
                            ))}
                        </svg>

                        {/* Interactive Tooltip */}
                        {hoveredPeriod && (
                            <div style={{
                                position: "absolute",
                                top: "10px",
                                right: "10px",
                                background: "#111827",
                                border: "1px solid #3B82F6",
                                padding: "8px 12px",
                                borderRadius: "6px",
                                fontSize: "11px",
                                pointerEvents: "none",
                                boxShadow: "0 4px 12px rgba(0,0,0,0.5)"
                            }}>
                                <div><strong>{hoveredPeriod.period}: {hoveredPeriod.subject}</strong></div>
                                <div style={{ color: "var(--success)", marginTop: "2px" }}>
                                    Attendance: {hoveredPeriod.rate}% ({hoveredPeriod.present} students)
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* 2. MULTIMODAL DISTRIBUTION & STABILITY */}
                <div className="panel-card" style={{ background: "#0E1526" }}>
                    <div className="panel-title">
                        <span>Attendance Classification</span>
                        <span style={{ fontSize: "11px", color: "var(--muted)" }}>500 Students</span>
                    </div>

                    {/* Segmented Distribution Bar */}
                    <div style={{
                        height: "14px",
                        width: "100%",
                        background: "#1E293B",
                        borderRadius: "7px",
                        display: "flex",
                        overflow: "hidden",
                        marginBottom: "12px"
                    }}>
                        <div style={{ width: "86%", background: "var(--success)" }} title="Present: 86%"></div>
                        <div style={{ width: "8%", background: "var(--warning)" }} title="Partial: 8%"></div>
                        <div style={{ width: "4%", background: "var(--danger)" }} title="Absent: 4%"></div>
                        <div style={{ width: "2%", background: "#8B5CF6" }} title="Uncertain: 2%"></div>
                    </div>

                    {/* Legend Breakdown */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--success)" }}></span>
                            <span style={{ color: "var(--muted)" }}>Present:</span>
                            <strong style={{ color: "var(--text)", fontFamily: "monospace" }}>296 (86%)</strong>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--warning)" }}></span>
                            <span style={{ color: "var(--muted)" }}>Partial:</span>
                            <strong style={{ color: "var(--text)", fontFamily: "monospace" }}>28 (8%)</strong>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--danger)" }}></span>
                            <span style={{ color: "var(--muted)" }}>Absent:</span>
                            <strong style={{ color: "var(--text)", fontFamily: "monospace" }}>14 (4%)</strong>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#8B5CF6" }}></span>
                            <span style={{ color: "var(--muted)" }}>Uncertain:</span>
                            <strong style={{ color: "var(--text)", fontFamily: "monospace" }}>7 (2%)</strong>
                        </div>
                    </div>

                    {/* Camera FPS Jitter Sparkline */}
                    <div style={{ marginTop: "14px", paddingTop: "10px", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                            <span style={{ color: "var(--muted)" }}>FPS Stability (10s Jitter):</span>
                            <strong style={{ color: "var(--primary-light)", fontFamily: "monospace" }}>25.1 FPS (±0.2)</strong>
                        </div>
                        <svg viewBox={`0 0 ${fpsSvgWidth} ${fpsSvgHeight}`} style={{ width: "100%", height: "24px" }}>
                            <polyline
                                fill="none"
                                stroke="#10B981"
                                strokeWidth="2"
                                points={fpsPointsCoords}
                            />
                        </svg>
                    </div>
                </div>
            </div>
        </div>
    );
}
