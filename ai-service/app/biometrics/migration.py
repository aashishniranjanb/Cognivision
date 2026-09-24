"""Migration utility to import legacy students from JSON registry to V1.3 SQLite Biometric Database."""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from app.biometrics.database import BiometricDatabase, resolve_db_path
from app.biometrics.repository import BiometricRepository
from app.biometrics.schemas import StudentCreate, BiometricProfileBase

def run_migration(
    json_path: str = "data/registry/students.json",
    db_path: str = "data/biometrics/student_biometrics.db"
) -> Dict[str, Any]:
    """Migrates existing student records from JSON registry to the SQLite database."""
    here = Path(__file__).resolve()
    ai_root = here.parent.parent.parent
    full_json_path = ai_root / json_path if not Path(json_path).is_absolute() else Path(json_path)

    db = BiometricDatabase(db_path=str(ai_root / db_path) if not Path(db_path).is_absolute() else db_path)
    repo = BiometricRepository(db=db)

    migrated_count = 0
    skipped_count = 0
    errors: List[str] = []

    if not full_json_path.exists():
        return {
            "status": "warning",
            "message": f"Registry file not found at {full_json_path}",
            "migrated": 0,
            "skipped": 0,
            "errors": [f"File not found: {full_json_path}"]
        }

    try:
        with open(full_json_path, "r", encoding="utf-8") as f:
            students_data = json.load(f)

        for sid, rec in students_data.items():
            try:
                existing = repo.get_student(sid)
                if existing:
                    skipped_count += 1
                    continue

                student_in = StudentCreate(
                    student_id=rec.get("student_id", sid),
                    register_number=rec.get("register_number", f"RA23{sid}"),
                    name=rec.get("name", f"Student {sid}"),
                    department=rec.get("department", "ECE"),
                    year=rec.get("year", 4),
                    section=rec.get("section", "A"),
                    status="ACTIVE" if rec.get("active", True) else "INACTIVE"
                )
                repo.create_student(student_in)

                # Initialize biometric profile
                emb_count = rec.get("embedding_count", 0)
                profile_status = "READY" if emb_count > 0 else "PENDING"
                repo.upsert_biometric_profile(
                    student_id=sid,
                    enrollment_quality=0.88 if emb_count > 0 else 0.0,
                    enrolled_images=emb_count,
                    status=profile_status
                )
                migrated_count += 1
            except Exception as item_err:
                errors.append(f"Failed to migrate student {sid}: {str(item_err)}")

        return {
            "status": "success",
            "message": f"Migration complete: {migrated_count} migrated, {skipped_count} skipped.",
            "migrated": migrated_count,
            "skipped": skipped_count,
            "total_in_registry": len(students_data),
            "errors": errors
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed reading registry JSON: {str(e)}",
            "migrated": migrated_count,
            "skipped": skipped_count,
            "errors": [str(e)]
        }

if __name__ == "__main__":
    result = run_migration()
    print("[V1.3 Biometrics Migration]", json.dumps(result, indent=2))
