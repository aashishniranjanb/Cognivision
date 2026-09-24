import Link from "next/link";
import { useRouter } from "next/router";

export default function Layout({ children }) {
    const router = useRouter();

    const navItems = [
        { href: "/", label: "Dashboard", icon: "▦" },
        { href: "/live", label: "Live Monitoring", icon: "◉" },
        { href: "/students", label: "Students", icon: "👥" },
        { href: "/classrooms", label: "Classrooms", icon: "🏢" },
        { href: "/cameras", label: "Cameras", icon: "📷" },
        { href: "/reports", label: "Reports", icon: "📄" },
    ];

    return (
        <div className="app">
            <aside className="sidebar">
                <div className="brand">
                    <div className="brand-icon">AI</div>
                    <div>
                        <h2>AttendAI</h2>
                        <span>Smart Attendance</span>
                    </div>
                </div>

                <nav className="navigation">
                    {navItems.map((item) => {
                        const isActive = router.pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`nav-item ${isActive ? "active" : ""}`}
                                style={{ textDecoration: "none" }}
                            >
                                <span>{item.icon}</span>
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="sidebar-bottom">
                    <div className="system-small">
                        <div className="online-dot"></div>
                        <div>
                            <strong>Vision Edge Core</strong>
                            <small>10/10 Cameras Online</small>
                        </div>
                    </div>
                </div>
            </aside>

            <main className="main-content">
                {children}
            </main>
        </div>
    );
}
