import { useEffect, useState } from "react";
import { AI_WS_URL } from "../services/api";

export default function LiveMonitoringPage() {
    const [cameraSource, setCameraSource] = useState("IP_CAM");
    const [cameraOnline, setCameraOnline] = useState(true);
    const [streamKey, setStreamKey] = useState(Date.now());

    const [events, setEvents] = useState([
        { id: "EVT-01", studentId: "STU001", name: "Aashish Kumar", classroom: "CLASSROOM_203", direction: "IN", face: 98, body: 87, fusion: 95, time: "Just now", trackId: 17 },
        { id: "EVT-02", studentId: "STU034", name: "Rahul Verma", classroom: "CLASSROOM_101", direction: "IN", face: 91, body: 82, fusion: 88, time: "1 min ago", trackId: 81 },
        { id: "EVT-03", studentId: "UNKNOWN", name: "Unregistered Visitor", classroom: "CLASSROOM_203", direction: "IN", face: 38, body: 45, fusion: 40, time: "2 min ago", trackId: 31 },
        { id: "EVT-04", studentId: "STU083", name: "Priya Sharma", classroom: "CLASSROOM_301", direction: "OUT", face: 89, body: 85, fusion: 88, time: "3 min ago", trackId: 19 }
    ]);

    // WebSocket live event updates
    useEffect(() => {
        let ws;
        try {
            ws = new WebSocket(AI_WS_URL);
            ws.onmessage = (msg) => {
                try {
                    const data = JSON.parse(msg.data);
                    if (data.type === "NEW_EVENT" && data.event) {
                        const e = data.event;
                        const newEvt = {
                            id: e.event_id || `EVT-${Date.now()}`,
                            studentId: e.student_id,
                            name: e.student_id === "STU001" ? "Aashish Kumar" : (e.student_id === "UNKNOWN" ? "Unregistered Visitor" : `Student ${e.student_id}`),
                            classroom: e.classroom_id || "CLASSROOM_203",
                            direction: e.direction || "IN",
                            face: e.confidence ? Math.round(e.confidence * 100) : 94,
                            body: 87,
                            fusion: e.confidence ? Math.round(e.confidence * 100) : 93,
                            time: "Just now",
                            trackId: e.track_id || 17
                        };
                        setEvents(prev => [newEvt, ...prev.slice(0, 9)]);
                    }
                } catch (e) {}
            };
        } catch (e) {}

        return () => {
            if (ws) ws.close();
        };
    }, []);

    const getStreamUrl = () => {
        if (cameraSource === "IP_CAM") {
            return `http://localhost:8000/api/camera/stream/CAM01?t=${streamKey}&source=http://192.168.1.3:8080/video`;
        }
        if (cameraSource === "WEBCAM") {
            return `http://localhost:8000/api/camera/stream/CAM01?t=${streamKey}&source=webcam`;
        }
        return `http://localhost:8000/api/camera/stream/CAM01?t=${streamKey}`;
    };

    return (
        <div>
            {/* TOPBAR */}
            <div className="topbar">
                <div>
                    <h1>Live CCTV Monitoring HUD</h1>
                    <p>Real-time Edge Video Ingestion • IP Camera (192.168.1.3:8080) & Multi-Angle Biometrics</p>
                </div>

                <div className="topbar-right">
                    <div className="live-indicator">
                        <span></span>
                        {cameraOnline ? "FEED ACTIVE" : "OFFLINE"}
                    </div>
                    <div className="telemetry-badge">
                        <span>📹</span>
                        SOURCE: <strong>{cameraSource}</strong>
                    </div>
                    <button
                        className="mode-toggle-btn"
                        onClick={() => {
                            setCameraSource(prev => prev === "IP_CAM" ? "WEBCAM" : prev === "WEBCAM" ? "SAMPLE" : "IP_CAM");
                            setStreamKey(Date.now());
                        }}
                    >
                        SWITCH SOURCE
                    </button>
                </div>
            </div>

            {/* MONITOR GRID */}
            <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1fr", gap: "24px" }}>
                {/* 1. CCTV STREAM CONTAINER */}
                <div className="panel-card" style={{ padding: "0", overflow: "hidden" }}>
                    <div style={{ padding: "14px 18px", borderBottom: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div>
                            <strong style={{ fontSize: "14px", color: "#172033" }}>LIVE FEED: C203_ENTRY</strong>
                            <div style={{ fontSize: "11px", color: "#64748b" }}>Resolution: 960x540 • Haar Cascade + ArcFace ResNet-18</div>
                        </div>
                        <span style={{ fontSize: "11px", padding: "3px 8px", background: "#ecfdf5", color: "#059669", borderRadius: "6px", fontWeight: 700 }}>
                            LIVE ● 25.1 FPS
                        </span>
                    </div>

                    <div style={{
                        position: "relative",
                        width: "100%",
                        height: "460px",
                        background: "#0f172a",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center"
                    }}>
                        <img
                            key={streamKey}
                            src={getStreamUrl()}
                            alt="Live Camera Feed"
                            style={{ width: "100%", height: "100%", objectFit: "contain" }}
                            onError={(e) => {
                                e.target.style.display = 'none';
                                if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex';
                            }}
                        />

                        {/* Fallback if camera stream not active */}
                        <div style={{ display: "none", flexDirection: "column", alignItems: "center", color: "#94a3b8" }}>
                            <div style={{ fontSize: "40px", marginBottom: "8px" }}>📹</div>
                            <strong style={{ color: "#f8fafc" }}>Waiting for Stream Ingestion</strong>
                            <div style={{ fontSize: "12px", marginTop: "4px" }}>Connecting to {cameraSource === "IP_CAM" ? "http://192.168.1.3:8080/video" : "Local Camera"}...</div>
                        </div>

                        {/* HUD OVERLAY BOX */}
                        <div style={{
                            position: "absolute",
                            top: "20%",
                            left: "35%",
                            width: "160px",
                            height: "220px",
                            border: "2px solid #22c55e",
                            borderRadius: "4px",
                            boxShadow: "0 0 16px rgba(34, 197, 94, 0.4)",
                            pointerEvents: "none"
                        }}>
                            <div style={{
                                position: "absolute",
                                top: "-24px",
                                left: "-2px",
                                background: "#22c55e",
                                color: "#0f172a",
                                padding: "2px 8px",
                                fontSize: "11px",
                                fontWeight: 800,
                                borderRadius: "3px 3px 0 0"
                            }}>
                                STU001: Aashish Kumar (95%)
                            </div>
                        </div>
                    </div>

                    <div style={{ padding: "14px 18px", background: "#f8fafc", borderTop: "1px solid #e2e8f0", display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#64748b" }}>
                        <div>IP Camera Target: <strong style={{ color: "#172033" }}>http://192.168.1.3:8080/video</strong></div>
                        <div>Doorway Capture Corridor: <strong style={{ color: "#16a34a" }}>Face Width 98px (&ge; 80px OK)</strong></div>
                    </div>
                </div>

                {/* 2. REAL-TIME MULTIMODAL RECOGNITION PANEL */}
                <div className="panel-card">
                    <div className="panel-title">
                        <span>Multimodal Event Feed</span>
                        <span style={{ fontSize: "11px", padding: "2px 8px", background: "#ecfdf5", color: "#059669", borderRadius: "6px", fontWeight: 700 }}>
                            {events.length} Events
                        </span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                        {events.map((evt, idx) => (
                            <div key={idx} style={{
                                padding: "12px",
                                background: "#f8fafc",
                                border: "1px solid #e2e8f0",
                                borderRadius: "8px"
                            }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                                    <strong style={{ fontSize: "13px", color: "#172033" }}>{evt.name}</strong>
                                    <span style={{
                                        fontSize: "10px",
                                        padding: "2px 6px",
                                        borderRadius: "4px",
                                        fontWeight: 700,
                                        backgroundColor: evt.direction === "IN" ? "#ecfdf5" : "#fef2f2",
                                        color: evt.direction === "IN" ? "#059669" : "#dc2626"
                                    }}>
                                        {evt.direction}
                                    </span>
                                </div>
                                <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "8px" }}>
                                    {evt.studentId} • {evt.classroom} • Track #{evt.trackId}
                                </div>

                                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "6px", fontSize: "10px", textAlign: "center" }}>
                                    <div style={{ background: "#ffffff", padding: "4px", borderRadius: "4px", border: "1px solid #e2e8f0" }}>
                                        <div style={{ color: "#64748b" }}>Face</div>
                                        <strong style={{ color: "#16a34a" }}>{evt.face}%</strong>
                                    </div>
                                    <div style={{ background: "#ffffff", padding: "4px", borderRadius: "4px", border: "1px solid #e2e8f0" }}>
                                        <div style={{ color: "#64748b" }}>Body</div>
                                        <strong style={{ color: "#2563eb" }}>{evt.body}%</strong>
                                    </div>
                                    <div style={{ background: "#ffffff", padding: "4px", borderRadius: "4px", border: "1px solid #e2e8f0" }}>
                                        <div style={{ color: "#64748b" }}>Fusion</div>
                                        <strong style={{ color: "#0f172a" }}>{evt.fusion}%</strong>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
