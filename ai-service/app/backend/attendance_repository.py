"""Persistent Attendance Repository leveraging local SQLite with Append-Only JSONL Audit logging."""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from app.events.event_schema import CampusEvent

class AttendanceRepository:
    def __init__(
        self,
        db_path: str = "data/attendance_records/attendance.db",
        audit_file: str = "audit/attendance_audit.jsonl"
    ):
        self.db_path = Path(db_path)
        self.audit_file = Path(audit_file)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 1. Events Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    timestamp_iso TEXT,
                    camera_id TEXT,
                    classroom_id TEXT,
                    track_id INTEGER,
                    event_type TEXT,
                    confidence REAL,
                    student_id TEXT,
                    metadata_json TEXT
                )
            """)
            # 2. Student Daily Attendance Records
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    student_id TEXT,
                    first_in REAL,
                    last_out REAL,
                    total_duration_sec REAL,
                    status TEXT,
                    UNIQUE(date, student_id)
                )
            """)
            # 3. Exceptions Audit Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_exceptions (
                    exception_id TEXT PRIMARY KEY,
                    timestamp REAL,
                    camera_id TEXT,
                    classroom_id TEXT,
                    anomaly_type TEXT,
                    track_id INTEGER,
                    confidence REAL,
                    student_id TEXT,
                    details TEXT
                )
            """)
            conn.commit()

    def save_event(self, event: CampusEvent):
        """Persists event to SQLite and writes immutable audit record to JSONL."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO events (
                    event_id, timestamp, timestamp_iso, camera_id, classroom_id,
                    track_id, event_type, confidence, student_id, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id,
                event.timestamp,
                event.timestamp_iso,
                event.camera_id,
                event.classroom_id,
                event.track_id,
                event.event_type,
                event.confidence,
                event.student_id,
                json.dumps(event.metadata)
            ))
            conn.commit()

        # Immutable append to audit log
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            print(f"[AttendanceRepository] Failed to append audit record: {e}")

    def get_recent_events(self, limit: int = 50, event_type: Optional[str] = None) -> List[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if event_type:
                cursor.execute("""
                    SELECT * FROM events WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?
                """, (event_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM events ORDER BY timestamp DESC LIMIT ?
                """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_student_events(self, student_id: str) -> List[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM events WHERE student_id = ? ORDER BY timestamp ASC
            """, (student_id,))
            return [dict(r) for r in cursor.fetchall()]

