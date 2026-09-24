"""Thread-safe Repository for Student, Biometric Profile, and Embedding Variant CRUD operations."""
from datetime import datetime, timezone
import numpy as np

from app.biometrics.database import BiometricDatabase
from app.biometrics.schemas import (
    StudentCreate, StudentUpdate, StudentResponse,
    BiometricProfileBase, BiometricProfileResponse,
    EmbeddingVariantCreate, EmbeddingVariantResponse,
    StudentDetailResponse, serialize_embedding, deserialize_embedding
)

class BiometricRepository:
    def __init__(self, db: Optional[BiometricDatabase] = None):
        self.db = db or BiometricDatabase()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # ==========================================
    # 1. STUDENTS CRUD
    # ==========================================
    def create_student(self, student_in: StudentCreate) -> StudentResponse:
        now = self._now()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO students (student_id, register_number, name, department, year, section, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_in.student_id,
                student_in.register_number,
                student_in.name,
                student_in.department,
                student_in.year,
                student_in.section,
                student_in.status,
                now,
                now
            ))
            # Also initialize an empty biometric profile
            cursor.execute("""
                INSERT OR IGNORE INTO student_biometric_profiles (
                    student_id, embedding_model, embedding_dimension, template_version,
                    enrollment_quality, enrolled_images, status, updated_at
                ) VALUES (?, 'ArcFace-512', 512, 1, 0.0, 0, 'PENDING', ?)
            """, (student_in.student_id, now))
            conn.commit()

        return self.get_student(student_in.student_id)

    def get_student(self, student_id: str) -> Optional[StudentResponse]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, p.status as biometric_status, p.enrolled_images, p.enrollment_quality
                FROM students s
                LEFT JOIN student_biometric_profiles p ON s.student_id = p.student_id
                WHERE s.student_id = ?
            """, (student_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return StudentResponse(
                student_id=row["student_id"],
                register_number=row["register_number"],
                name=row["name"],
                department=row["department"],
                year=row["year"],
                section=row["section"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                biometric_status=row["biometric_status"] or "PENDING",
                enrolled_images=row["enrolled_images"] or 0,
                enrollment_quality=row["enrollment_quality"] or 0.0
            )

    def update_student(self, student_id: str, student_in: StudentUpdate) -> Optional[StudentResponse]:
        existing = self.get_student(student_id)
        if not existing:
            return None

        fields = []
        values = []
        dump_data = getattr(student_in, "model_dump", None)
        data_dict = dump_data(exclude_unset=True) if callable(dump_data) else student_in.dict(exclude_unset=True)
        for k, v in data_dict.items():
            if v is not None:
                fields.append(f"{k} = ?")
                values.append(v)

        if not fields:
            return existing

        now = self._now()
        fields.append("updated_at = ?")
        values.append(now)
        values.append(student_id)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE students SET {', '.join(fields)} WHERE student_id = ?"
            cursor.execute(query, tuple(values))
            conn.commit()

        return self.get_student(student_id)

    def delete_student(self, student_id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_students(
        self,
        search: Optional[str] = None,
        department: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[StudentResponse]:
        clauses = []
        params = []

        if search:
            clauses.append("(s.student_id LIKE ? OR s.name LIKE ? OR s.register_number LIKE ?)")
            term = f"%{search}%"
            params.extend([term, term, term])

        if department and department != "ALL":
            clauses.append("s.department = ?")
            params.append(department)

        if year:
            clauses.append("s.year = ?")
            params.append(year)

        if status and status != "ALL":
            clauses.append("s.status = ?")
            params.append(status)

        where = "WHERE " + " AND ".join(clauses) if clauses else ""

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = f"""
                SELECT s.*, p.status as biometric_status, p.enrolled_images, p.enrollment_quality
                FROM students s
                LEFT JOIN student_biometric_profiles p ON s.student_id = p.student_id
                {where}
                ORDER BY s.student_id ASC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, skip])
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [
                StudentResponse(
                    student_id=r["student_id"],
                    register_number=r["register_number"],
                    name=r["name"],
                    department=r["department"],
                    year=r["year"],
                    section=r["section"],
                    status=r["status"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    biometric_status=r["biometric_status"] or "PENDING",
                    enrolled_images=r["enrolled_images"] or 0,
                    enrollment_quality=r["enrollment_quality"] or 0.0
                )
                for r in rows
            ]

    # ==========================================
    # 2. BIOMETRIC PROFILE CRUD
    # ==========================================
    def get_biometric_profile(self, student_id: str) -> Optional[BiometricProfileResponse]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM student_biometric_profiles WHERE student_id = ?
            """, (student_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return BiometricProfileResponse(
                student_id=row["student_id"],
                embedding_model=row["embedding_model"],
                embedding_dimension=row["embedding_dimension"],
                template_version=row["template_version"],
                enrollment_quality=row["enrollment_quality"],
                enrolled_images=row["enrolled_images"],
                status=row["status"],
                has_template=row["template_embedding"] is not None,
                updated_at=row["updated_at"]
            )

    def get_template_embedding(self, student_id: str) -> Optional[List[float]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT template_embedding FROM student_biometric_profiles WHERE student_id = ?
            """, (student_id,))
            row = cursor.fetchone()
            if not row or not row["template_embedding"]:
                return None
            return deserialize_embedding(row["template_embedding"])

    def upsert_biometric_profile(
        self,
        student_id: str,
        template_embedding: Optional[List[float]] = None,
        template_version: Optional[int] = None,
        enrollment_quality: float = 0.0,
        enrolled_images: int = 0,
        status: str = "READY",
        embedding_model: str = "ArcFace-512",
        archive_notes: Optional[str] = None
    ) -> BiometricProfileResponse:
        now = self._now()
        raw_blob = serialize_embedding(template_embedding) if template_embedding else None

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Check existing profile for version increment & archiving
            cursor.execute("SELECT * FROM student_biometric_profiles WHERE student_id = ?", (student_id,))
            existing = cursor.fetchone()

            if existing and existing["template_embedding"] and raw_blob and template_version is None:
                # Archive previous template version to history
                cursor.execute("""
                    INSERT INTO student_template_history (
                        student_id, template_version, template_embedding,
                        enrollment_quality, enrolled_images, created_at, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_id,
                    existing["template_version"],
                    existing["template_embedding"],
                    existing["enrollment_quality"],
                    existing["enrolled_images"],
                    existing["updated_at"],
                    archive_notes or f"Archived prior to v{existing['template_version'] + 1} update"
                ))
                next_version = existing["template_version"] + 1
            elif template_version is not None:
                next_version = template_version
            else:
                next_version = 1

            cursor.execute("""
                INSERT INTO student_biometric_profiles (
                    student_id, embedding_model, embedding_dimension, template_embedding,
                    template_version, enrollment_quality, enrolled_images, status, updated_at
                ) VALUES (?, ?, 512, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id) DO UPDATE SET
                    template_embedding = COALESCE(excluded.template_embedding, student_biometric_profiles.template_embedding),
                    template_version = excluded.template_version,
                    enrollment_quality = excluded.enrollment_quality,
                    enrolled_images = excluded.enrolled_images,
                    status = excluded.status,
                    embedding_model = excluded.embedding_model,
                    updated_at = excluded.updated_at
            """, (
                student_id, embedding_model, raw_blob, next_version,
                enrollment_quality, enrolled_images, status, now
            ))
            conn.commit()

        return self.get_biometric_profile(student_id)

    def get_template_history(self, student_id: str) -> List[Any]:
        from app.biometrics.schemas import TemplateHistoryResponse
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM student_template_history
                WHERE student_id = ?
                ORDER BY template_version DESC
            """, (student_id,))
            rows = cursor.fetchall()
            return [
                TemplateHistoryResponse(
                    id=r["id"],
                    student_id=r["student_id"],
                    template_version=r["template_version"],
                    enrollment_quality=r["enrollment_quality"],
                    enrolled_images=r["enrolled_images"],
                    created_at=r["created_at"],
                    notes=r["notes"]
                )
                for r in rows
            ]

    def rollback_template(self, student_id: str, target_version: int) -> Optional[BiometricProfileResponse]:
        """Rolls back a student's biometric template to an earlier archived version."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM student_template_history
                WHERE student_id = ? AND template_version = ?
            """, (student_id, target_version))
            hist = cursor.fetchone()
            if not hist:
                return None

            now = self._now()
            # Upsert current profile with target historical template
            cursor.execute("""
                UPDATE student_biometric_profiles
                SET template_embedding = ?,
                    template_version = ?,
                    enrollment_quality = ?,
                    enrolled_images = ?,
                    status = 'READY',
                    updated_at = ?
                WHERE student_id = ?
            """, (
                hist["template_embedding"],
                hist["template_version"],
                hist["enrollment_quality"],
                hist["enrolled_images"],
                now,
                student_id
            ))
            conn.commit()

        return self.get_biometric_profile(student_id)

    # ==========================================
    # 3. EMBEDDING VARIANTS CRUD
    # ==========================================
    def add_variant(self, student_id: str, variant_in: EmbeddingVariantCreate) -> EmbeddingVariantResponse:
        now = self._now()
        raw_blob = serialize_embedding(variant_in.embedding)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO student_embedding_variants (
                    student_id, embedding, face_width, blur_score, illumination_score,
                    yaw, pitch, roll, detection_confidence, quality_score, source_image, pose_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                student_id, raw_blob, variant_in.face_width, variant_in.blur_score,
                variant_in.illumination_score, variant_in.yaw, variant_in.pitch, variant_in.roll,
                variant_in.detection_confidence, variant_in.quality_score, variant_in.source_image,
                getattr(variant_in, "pose_type", "FRONTAL") or "FRONTAL", now
            ))
            variant_id = cursor.lastrowid

            # Update enrolled_images count in profile
            cursor.execute("""
                UPDATE student_biometric_profiles
                SET enrolled_images = (
                    SELECT COUNT(*) FROM student_embedding_variants WHERE student_id = ?
                ),
                updated_at = ?
                WHERE student_id = ?
            """, (student_id, now, student_id))
            conn.commit()

        return self.get_variant(variant_id)

    def get_variant(self, variant_id: int) -> Optional[EmbeddingVariantResponse]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM student_embedding_variants WHERE id = ?", (variant_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return EmbeddingVariantResponse(
                id=row["id"],
                student_id=row["student_id"],
                face_width=row["face_width"],
                blur_score=row["blur_score"],
                illumination_score=row["illumination_score"],
                yaw=row["yaw"],
                pitch=row["pitch"],
                roll=row["roll"],
                detection_confidence=row["detection_confidence"],
                quality_score=row["quality_score"],
                source_image=row["source_image"],
                pose_type=row["pose_type"] if "pose_type" in row.keys() and row["pose_type"] else "FRONTAL",
                created_at=row["created_at"]
            )

    def list_variants(self, student_id: str) -> List[EmbeddingVariantResponse]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM student_embedding_variants
                WHERE student_id = ?
                ORDER BY quality_score DESC, id ASC
            """, (student_id,))
            rows = cursor.fetchall()
            return [
                EmbeddingVariantResponse(
                    id=r["id"],
                    student_id=r["student_id"],
                    face_width=r["face_width"],
                    blur_score=r["blur_score"],
                    illumination_score=r["illumination_score"],
                    yaw=r["yaw"],
                    pitch=r["pitch"],
                    roll=r["roll"],
                    detection_confidence=r["detection_confidence"],
                    quality_score=r["quality_score"],
                    source_image=r["source_image"],
                    pose_type=r["pose_type"] if "pose_type" in r.keys() and r["pose_type"] else "FRONTAL",
                    created_at=r["created_at"]
                )
                for r in rows
            ]

    def get_variant_embeddings(self, student_id: str) -> List[Tuple[int, List[float], str, float]]:
        """Returns list of (variant_id, 512-dim embedding, pose_type, quality_score) for multi-angle matching."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, embedding, pose_type, quality_score FROM student_embedding_variants
                WHERE student_id = ?
                ORDER BY quality_score DESC
            """, (student_id,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                emb = deserialize_embedding(r["embedding"])
                pose = r["pose_type"] if "pose_type" in r.keys() and r["pose_type"] else "FRONTAL"
                results.append((r["id"], emb, pose, r["quality_score"]))
            return results

    def delete_variant(self, variant_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT student_id FROM student_embedding_variants WHERE id = ?", (variant_id,))
            row = cursor.fetchone()
            if not row:
                return False
            student_id = row["student_id"]
            cursor.execute("DELETE FROM student_embedding_variants WHERE id = ?", (variant_id,))

            now = self._now()
            cursor.execute("""
                UPDATE student_biometric_profiles
                SET enrolled_images = (
                    SELECT COUNT(*) FROM student_embedding_variants WHERE student_id = ?
                ),
                updated_at = ?
                WHERE student_id = ?
            """, (student_id, now, student_id))
            conn.commit()
            return True

    # ==========================================
    # 4. STUDENT DETAIL VIEW
    # ==========================================
    def get_student_detail(self, student_id: str) -> Optional[StudentDetailResponse]:
        student = self.get_student(student_id)
        if not student:
            return None
        profile = self.get_biometric_profile(student_id)
        variants = self.list_variants(student_id)
        history = self.get_template_history(student_id)

        return StudentDetailResponse(
            student_id=student.student_id,
            register_number=student.register_number,
            name=student.name,
            department=student.department,
            year=student.year,
            section=student.section,
            status=student.status,
            created_at=student.created_at,
            updated_at=student.updated_at,
            biometric_status=student.biometric_status,
            enrolled_images=student.enrolled_images,
            enrollment_quality=student.enrollment_quality,
            biometric_profile=profile,
            variants=variants,
            template_history=history
        )
