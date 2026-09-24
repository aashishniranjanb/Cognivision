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

    const svgWidth = 500;
    const svgHeight = 120;
    const padX = 40;
    const padY = 20;

    const points = periodData.map((d, i) => {
        const x = padX + (i * (svgWidth - 2 * padX)) / (periodData.length - 1);
        const norm = (d.rate - 70) / 30;
        const y = svgHeight - padY - norm * (svgHeight - 2 * padY);
        return { ...d, x, y };
    });

    const pathD = points.reduce((acc, pt, i) => {
        return i === 0 ? `M ${pt.x},${pt.y}` : `${acc} L ${pt.x},${pt.y}`;
    }, "");

    const areaD = `${pathD} L ${points[points.length - 1].x},${svgHeight - padY} L ${points[0].x},${svgHeight - padY} Z`;

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
                <div className="panel-card" style={{ background: "#ffffff", border: "1px solid #e9edf3" }}>
                    <div className="panel-title">
                        <span>Period Attendance Trend (P1 → P5)</span>
                        <span style={{ fontSize: "11px", color: "#16a34a", fontWeight: 600 }}>
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
                                    <stop offset="0%" stopColor="#2563EB" stopOpacity="0.25" />
                                    <stop offset="100%" stopColor="#2563EB" stopOpacity="0.0" />
                                </linearGradient>
                            </defs>

                            <line x1={padX} y1={padY} x2={svgWidth - padX} y2={padY} stroke="#e2e8f0" strokeDasharray="3 3" />
                            <line x1={padX} y1={svgHeight / 2} x2={svgWidth - padX} y2={svgHeight / 2} stroke="#e2e8f0" strokeDasharray="3 3" />
                            <line x1={padX} y1={svgHeight - padY} x2={svgWidth - padX} y2={svgHeight - padY} stroke="#cbd5e1" />

                            <path d={areaD} fill="url(#trendGradient)" />
                            <path d={pathD} fill="none" stroke="#2563EB" strokeWidth="2.5" strokeLinecap="round" />

                            {points.map((pt, i) => (
                                <g key={i}>
                                    <circle
                                        cx={pt.x}
                                        cy={pt.y}
                                        r={hoveredPeriod?.period === pt.period ? 6 : 4}
                                        fill={hoveredPeriod?.period === pt.period ? "#ffffff" : "#2563EB"}
                                        stroke="#1D4ED8"
                                        strokeWidth="2"
                                        style={{ cursor: "pointer", transition: "all 0.2s" }}
                                        onMouseEnter={() => setHoveredPeriod(pt)}
                                        onMouseLeave={() => setHoveredPeriod(null)}
                                    />
                                    <text
                                        x={pt.x}
                                        y={svgHeight - 4}
                                        fill="#64748B"
                                        fontSize="11"
                                        fontWeight="600"
                                        textAnchor="middle"
                                    >
                                        {pt.period}
                                    </text>
                                </g>
                            ))}
                        </svg>

                        {hoveredPeriod && (
                            <div style={{
                                position: "absolute",
                                left: `${(hoveredPeriod.x / svgWidth) * 100}%`,
                                top: "-10px",
                                transform: "translate(-50%, -100%)",
                                background: "#0F172A",
                                color: "#FFFFFF",
                                padding: "6px 10px",
                                borderRadius: "6px",
                                fontSize: "11px",
                                pointerEvents: "none",
                                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                                whiteSpace: "nowrap"
                            }}>
                                <strong>{hoveredPeriod.period}: {hoveredPeriod.subject}</strong>
                                <div style={{ color: "#38BDF8" }}>{hoveredPeriod.rate}% ({hoveredPeriod.present} present)</div>
                            </div>
                        )}
                    </div>
                </div>

                {/* 2. CLASSIFICATION BREAKDOWN & FPS SPARKLINE */}
                <div className="panel-card" style={{ background: "#ffffff", border: "1px solid #e9edf3" }}>
                    <div className="panel-title">
                        <span>Multimodal Classification Status</span>
                        <span style={{ fontSize: "11px", color: "#64748b" }}>Real-time</span>
                    </div>

                    <div style={{ display: "flex", height: "14px", borderRadius: "6px", overflow: "hidden", marginBottom: "16px" }}>
                        <div style={{ width: "86%", background: "#16A34A" }} title="Confirmed Present (86%)"></div>
                        <div style={{ width: "8%", background: "#F59E0B" }} title="Partial Session (8%)"></div>
                        <div style={{ width: "4%", background: "#94A3B8" }} title="Confirmed Absent (4%)"></div>
                        <div style={{ width: "2%", background: "#DC2626" }} title="Identity Uncertain (2%)"></div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "8px", fontSize: "12px", marginBottom: "16px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#16A34A" }}></span>
                            <span style={{ color: "#475569" }}>Present: <strong>86%</strong></span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#F59E0B" }}></span>
                            <span style={{ color: "#475569" }}>Partial: <strong>8%</strong></span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#94A3B8" }}></span>
                            <span style={{ color: "#475569" }}>Absent: <strong>4%</strong></span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#DC2626" }}></span>
                            <span style={{ color: "#475569" }}>Uncertain: <strong>2%</strong></span>
                        </div>
                    </div>

                    {/* FPS Sparkline */}
                    <div style={{ borderTop: "1px solid #e2e8f0", paddingTop: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div>
                            <div style={{ fontSize: "11px", color: "#64748B" }}>FPS Jitter (10s)</div>
                            <div style={{ fontSize: "14px", fontWeight: "700", color: "#0F172A" }}>25.1 ± 0.2 FPS</div>
                        </div>
                        <svg width={fpsSvgWidth} height={fpsSvgHeight} style={{ overflow: "visible" }}>
                            <polyline
                                fill="none"
                                stroke="#16A34A"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                points={fpsPointsCoords}
                            />
                        </svg>
                    </div>
                </div>
            </div>
        </div>
    );
}
