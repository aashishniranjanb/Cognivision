"""SQLite database layer for V1.3 Student Biometric Database."""
import sqlite3
import os
from pathlib import Path
from typing import Optional

def resolve_db_path(path_str: str = "data/biometrics/student_biometrics.db") -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    here = Path(__file__).resolve()
    # Find ai-service root
    ai_service_root = here.parent.parent.parent
    return ai_service_root / path_str

class BiometricDatabase:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = resolve_db_path()
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # 1. Students Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id TEXT PRIMARY KEY,
                    register_number TEXT UNIQUE,
                    name TEXT NOT NULL,
                    department TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    section TEXT DEFAULT 'A',
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 2. Biometric Profiles Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_biometric_profiles (
                    student_id TEXT PRIMARY KEY,
                    embedding_model TEXT NOT NULL DEFAULT 'ArcFace-512',
                    embedding_dimension INTEGER NOT NULL DEFAULT 512,
                    template_embedding BLOB,
                    template_version INTEGER NOT NULL DEFAULT 1,
                    enrollment_quality REAL NOT NULL DEFAULT 0.0,
                    enrolled_images INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
                )
            """)

            # 3. Embedding Variants Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_embedding_variants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    face_width REAL,
                    blur_score REAL,
                    illumination_score REAL,
                    yaw REAL,
                    pitch REAL,
                    roll REAL,
                    detection_confidence REAL,
                    quality_score REAL NOT NULL DEFAULT 0.0,
                    source_image TEXT,
                    pose_type TEXT DEFAULT 'FRONTAL',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
                )
            """)

            # 4. Template History Table for Versioning (Task 17)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_template_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    template_version INTEGER NOT NULL,
                    template_embedding BLOB NOT NULL,
                    enrollment_quality REAL NOT NULL,
                    enrolled_images INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    notes TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE
                )
            """)

            # Ensure pose_type column exists if table was previously created without it
            cursor.execute("PRAGMA table_info(student_embedding_variants)")
            cols = [row[1] for row in cursor.fetchall()]
            if "pose_type" not in cols:
                try:
                    cursor.execute("ALTER TABLE student_embedding_variants ADD COLUMN pose_type TEXT DEFAULT 'FRONTAL'")
                except Exception:
                    pass

            # 5. Indexes for high-throughput queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department, year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_status ON students(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_variants_student ON student_embedding_variants(student_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_status ON student_biometric_profiles(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_template_history_student ON student_template_history(student_id)")
            conn.commit()
        finally:
            conn.close()
