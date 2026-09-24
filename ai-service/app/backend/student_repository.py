"""Student Repository managing enrolled student identities, metadata, and roster lookups with SQLite Biometrics DB support."""
from typing import List, Optional, Dict
from app.enrollment.registry import StudentRegistry, StudentRecord
from app.biometrics.repository import BiometricRepository

class StudentRepository:
    def __init__(self, registry_file: str = "data/registry/students.json", biometric_repo: Optional[BiometricRepository] = None):
        self.registry = StudentRegistry(registry_file=registry_file)
        self.biometric_repo = biometric_repo or BiometricRepository()

    def get_student(self, student_id: str) -> Optional[StudentRecord]:
        db_student = self.biometric_repo.get_student(student_id)
        if db_student:
            return StudentRecord(
                student_id=db_student.student_id,
                name=db_student.name,
                department=db_student.department,
                year=db_student.year,
                active=(db_student.status == "ACTIVE"),
                enrolled_at=db_student.created_at,
                embedding_count=db_student.enrolled_images or 0
            )
        return self.registry.get(student_id)

    def list_students(self) -> List[StudentRecord]:
        records: Dict[str, StudentRecord] = {}
        # Load legacy first
        for s in self.registry.students.values():
            records[s.student_id] = s
        # Overlay/add database students
        db_students = self.biometric_repo.list_students(limit=1000)
        for dbs in db_students:
            records[dbs.student_id] = StudentRecord(
                student_id=dbs.student_id,
                name=dbs.name,
                department=dbs.department,
                year=dbs.year,
                active=(dbs.status == "ACTIVE"),
                enrolled_at=dbs.created_at,
                embedding_count=dbs.enrolled_images or 0
            )
        return list(records.values())

    def get_student_count(self) -> int:
        return len(self.list_students())


