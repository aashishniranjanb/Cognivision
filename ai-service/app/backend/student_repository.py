"""Student Repository managing enrolled student identities, metadata, and roster lookups."""
from typing import List, Optional, Dict
from app.enrollment.registry import StudentRegistry, StudentRecord

class StudentRepository:
    def __init__(self, registry_file: str = "data/registry/students.json"):
        self.registry = StudentRegistry(registry_file=registry_file)

    def get_student(self, student_id: str) -> Optional[StudentRecord]:
        return self.registry.get(student_id)

    def list_students(self) -> List[StudentRecord]:
        return list(self.registry.students.values())

    def get_student_count(self) -> int:
        return len(self.registry.students)

