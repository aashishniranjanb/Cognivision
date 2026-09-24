import { useState } from "react";

import Dashboard from "./pages/Dashboard";
import Students from "./pages/Students";
import LiveMonitoring from "./pages/LiveMonitoring";
import Cameras from "./pages/Cameras";
import Reports from "./pages/Reports";
import Classrooms from "./pages/Classrooms";

import "./App.css";

function App() {
    const [activePage, setActivePage] = useState("dashboard");

    const renderPage = () => {
        switch (activePage) {
            case "students":
                return <Students />;
            case "live":
                return <LiveMonitoring />;
            case "classrooms":
                return <Classrooms />;
            case "cameras":
                return <Cameras />;
            case "reports":
                return <Reports />;
            case "dashboard":
            default:
                return <Dashboard />;
        }
    };

    return (
        <div className="app">
            <aside className="sidebar">
                <div className="brand">
                    <div className="brand-icon">
                        VC
                    </div>
                    <div>
                        <h2>COMMAND CENTER</h2>
                        <span>SRM • AI Video Attendance</span>
                    </div>
                </div>

                <nav className="navigation">
                    <div
                        className={`nav-item ${activePage === "dashboard" ? "active" : ""}`}
                        onClick={() => setActivePage("dashboard")}
                    >
                        <span>▦</span>
                        Overview
                    </div>

                    <div
                        className={`nav-item ${activePage === "live" ? "active" : ""}`}
                        onClick={() => setActivePage("live")}
                    >
                        <span>◉</span>
                        Live CCTV Stream
                    </div>

                    <div
                        className={`nav-item ${activePage === "classrooms" ? "active" : ""}`}
                        onClick={() => setActivePage("classrooms")}
                    >
                        <span>▣</span>
                        Classrooms
                    </div>

                    <div
                        className={`nav-item ${activePage === "cameras" ? "active" : ""}`}
                        onClick={() => setActivePage("cameras")}
                    >
                        <span>📷</span>
                        Camera Health
                    </div>

                    <div
                        className={`nav-item ${activePage === "students" ? "active" : ""}`}
                        onClick={() => setActivePage("students")}
                    >
                        <span>👤</span>
                        Students & Audit
                    </div>

                    <div
                        className={`nav-item ${activePage === "reports" ? "active" : ""}`}
                        onClick={() => setActivePage("reports")}
                    >
                        <span>▤</span>
                        CSV & Period Reports
                    </div>
                </nav>

                <div className="sidebar-bottom">
                    <div className="system-small">
                        <span className="online-dot"></span>
                        <div>
                            <strong style={{ fontSize: "12px", color: "#F8FAFC" }}>
                                SYSTEM ONLINE
                            </strong>
                            <small style={{ display: "block", color: "#94A3B8", fontSize: "10px" }}>
                                10 / 10 Cameras Connected
                            </small>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="main-content">
                {renderPage()}
            </main>
        </div>
    );
}

export default App;