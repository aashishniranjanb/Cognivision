"""Student Registry module managing structured metadata separately from biometric vector embeddings."""
import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List

@dataclass
class StudentRecord:
    student_id: str
    name: str
    department: str
    year: int
    active: bool = True
    enrolled_at: Optional[str] = None
    embedding_count: int = 0

def _resolve_path(rel_path: str) -> Path:
    p = Path(rel_path)
    if p.is_absolute():
        return p
    here = Path(__file__).resolve()
    candidates = [
        p,
        here.parent.parent.parent.parent / rel_path,
        here.parent.parent.parent / rel_path,
        here.parent.parent / rel_path,
    ]
    for c in candidates:
        if c.exists():
            return c
    return here.parent.parent.parent.parent / rel_path

class StudentRegistry:
    def __init__(self, registry_file: str = "data/registry/students.json"):
        self.registry_file = _resolve_path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.students: Dict[str, StudentRecord] = {}
        self.load()

    def load(self):
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for sid, record in data.items():
                        self.students[sid] = StudentRecord(**record)
            except Exception as e:
                print(f"[StudentRegistry] Warning: Failed to load registry: {e}")
                self.students = {}
        else:
            self.save()

    def save(self):
        data = {sid: asdict(rec) for sid, rec in self.students.items()}
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register(self, student_id: str, name: str, department: str = "ECE", year: int = 4) -> StudentRecord:
        rec = StudentRecord(
            student_id=student_id,
            name=name,
            department=department,
            year=year,
            active=True
        )
        self.students[student_id] = rec
        self.save()
        return rec

    def get(self, student_id: str) -> Optional[StudentRecord]:
        return self.students.get(student_id)

    def list_all(self) -> List[StudentRecord]:
        return list(self.students.values())
