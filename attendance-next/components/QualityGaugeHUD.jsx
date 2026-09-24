import React from "react";

export default function QualityGaugeHUD({ metrics, targetPose = "FRONTAL", isPass = false }) {
    const {
        faceWidth = 0,
        sharpness = 0,
        illumination = 0,
        yaw = 0,
        pitch = 0,
        roll = 0,
        warning = null
    } = metrics || {};

    const minWidth = 80;
    const minSharpness = 100;
    const minIllum = 0.40;
    const maxIllum = 0.92;

    const widthPct = Math.min(100, Math.round((faceWidth / 150) * 100));
    const sharpnessPct = Math.min(100, Math.round((sharpness / 200) * 100));
    const illumPct = Math.min(100, Math.round((illumination / 1.0) * 100));

    // Calculate pose alignment score based on current target pose
    let poseDelta = 0;
    if (targetPose === "FRONTAL") poseDelta = Math.abs(yaw) + Math.abs(pitch);
    else if (targetPose === "LEFT_PROFILE") poseDelta = Math.abs(yaw - (-25));
    else if (targetPose === "RIGHT_PROFILE") poseDelta = Math.abs(yaw - 25);
    else if (targetPose === "TILT_UP") poseDelta = Math.abs(pitch - 15);
    else if (targetPose === "TILT_DOWN") poseDelta = Math.abs(pitch - (-15));

    const posePct = Math.max(0, Math.min(100, 100 - poseDelta * 2.5));

    return (
        <div style={{
            backgroundColor: "#ffffff",
            borderRadius: "10px",
            border: "1px solid #e2e8f0",
            padding: "16px",
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)"
        }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "14px", fontWeight: 700, color: "#1e293b" }}>Biometric Quality HUD</span>
                    <span style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: "12px",
                        backgroundColor: isPass ? "#ecfdf5" : "#fff7ed",
                        color: isPass ? "#059669" : "#c2410c",
                        border: `1px solid ${isPass ? "#a7f3d0" : "#ffedd5"}`
                    }}>
                        {isPass ? "✓ GATE PASSED" : "⚡ CALIBRATING"}
                    </span>
                </div>
                <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "monospace" }}>
                    Target: {targetPose}
                </span>
            </div>

            {/* GAUGES GRID */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                {/* Face Width Gauge */}
                <div style={{ padding: "10px", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                        <span style={{ color: "#475569" }}>Face Resolution</span>
                        <strong style={{ color: faceWidth >= minWidth ? "#059669" : "#dc2626" }}>
                            {Math.round(faceWidth)}px / {minWidth}px
                        </strong>
                    </div>
                    <div style={{ height: "6px", backgroundColor: "#e2e8f0", borderRadius: "3px", overflow: "hidden" }}>
                        <div style={{
                            width: `${widthPct}%`,
                            height: "100%",
                            backgroundColor: faceWidth >= minWidth ? "#10b981" : "#f59e0b",
                            transition: "width 0.2s ease"
                        }} />
                    </div>
                </div>

                {/* Sharpness Gauge */}
                <div style={{ padding: "10px", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                        <span style={{ color: "#475569" }}>Laplacian Sharpness</span>
                        <strong style={{ color: sharpness >= minSharpness ? "#059669" : "#dc2626" }}>
                            {Math.round(sharpness)} / {minSharpness}
                        </strong>
                    </div>
                    <div style={{ height: "6px", backgroundColor: "#e2e8f0", borderRadius: "3px", overflow: "hidden" }}>
                        <div style={{
                            width: `${sharpnessPct}%`,
                            height: "100%",
                            backgroundColor: sharpness >= minSharpness ? "#10b981" : "#ef4444",
                            transition: "width 0.2s ease"
                        }} />
                    </div>
                </div>

                {/* Illumination Gauge */}
                <div style={{ padding: "10px", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                        <span style={{ color: "#475569" }}>Illumination Contrast</span>
                        <strong style={{ color: (illumination >= minIllum && illumination <= maxIllum) ? "#059669" : "#d97706" }}>
                            {(illumination * 100).toFixed(0)}%
                        </strong>
                    </div>
                    <div style={{ height: "6px", backgroundColor: "#e2e8f0", borderRadius: "3px", overflow: "hidden" }}>
                        <div style={{
                            width: `${illumPct}%`,
                            height: "100%",
                            backgroundColor: (illumination >= minIllum && illumination <= maxIllum) ? "#10b981" : "#f59e0b",
                            transition: "width 0.2s ease"
                        }} />
                    </div>
                </div>

                {/* Pose Alignment Gauge */}
                <div style={{ padding: "10px", backgroundColor: "#f8fafc", borderRadius: "8px", border: "1px solid #f1f5f9" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                        <span style={{ color: "#475569" }}>Pose Alignment</span>
                        <strong style={{ color: posePct >= 75 ? "#059669" : "#2563eb" }}>
                            Yaw {yaw > 0 ? `+${yaw.toFixed(0)}` : yaw.toFixed(0)}° • Pitch {pitch.toFixed(0)}°
                        </strong>
                    </div>
                    <div style={{ height: "6px", backgroundColor: "#e2e8f0", borderRadius: "3px", overflow: "hidden" }}>
                        <div style={{
                            width: `${posePct}%`,
                            height: "100%",
                            backgroundColor: posePct >= 75 ? "#10b981" : "#3b82f6",
                            transition: "width 0.2s ease"
                        }} />
                    </div>
                </div>
            </div>

            {/* ADVISORY FEEDBACK CHIP */}
            {warning ? (
                <div style={{
                    padding: "8px 12px",
                    backgroundColor: "#fef2f2",
                    border: "1px solid #fecaca",
                    borderRadius: "6px",
                    color: "#b91c1c",
                    fontSize: "11px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px"
                }}>
                    <span>⚠️</span>
                    <span>{warning}</span>
                </div>
            ) : isPass ? (
                <div style={{
                    padding: "8px 12px",
                    backgroundColor: "#f0fdf4",
                    border: "1px solid #bbf7d0",
                    borderRadius: "6px",
                    color: "#166534",
                    fontSize: "11px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px"
                }}>
                    <span>✓</span>
                    <span>Pose & illumination optimal. Ready to capture biometric embedding.</span>
                </div>
            ) : (
                <div style={{
                    padding: "8px 12px",
                    backgroundColor: "#eff6ff",
                    border: "1px solid #bfdbfe",
                    borderRadius: "6px",
                    color: "#1e40af",
                    fontSize: "11px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px"
                }}>
                    <span>ℹ️</span>
                    <span>Position face within the oval guide for automatic multi-angle capture.</span>
                </div>
            )}
        </div>
    );
}
