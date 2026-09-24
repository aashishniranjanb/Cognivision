"""Pydantic schemas and dataclasses for V1.3 Student Biometric Database."""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np
import base64

class StudentBase(BaseModel):
    student_id: str = Field(..., description="Unique student identifier, e.g. STU001")
    register_number: Optional[str] = Field(None, description="Official registration number, e.g. RA23XXXXXXX")
    name: str = Field(..., description="Full legal name of the student")
    department: str = Field("ECE", description="Academic department (ECE, CSE, MECH, etc.)")
    year: int = Field(4, ge=1, le=5, description="Year of study (1 to 5)")
    section: str = Field("A", description="Class section (A, B, C, etc.)")
    status: str = Field("ACTIVE", description="Enrollment status: ACTIVE, INACTIVE, GRADUATED")

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    register_number: Optional[str] = None
    name: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    status: Optional[str] = None

class StudentResponse(StudentBase):
    created_at: str
    updated_at: str
    biometric_status: Optional[str] = "PENDING"
    enrolled_images: Optional[int] = 0
    enrollment_quality: Optional[float] = 0.0

class BiometricProfileBase(BaseModel):
    embedding_model: str = "ArcFace-512"
    embedding_dimension: int = 512
    template_version: int = 1
    enrollment_quality: float = 0.0
    enrolled_images: int = 0
    status: str = "PENDING"  # PENDING, READY, FLAGGED, RE_ENROLL_REQUIRED

class BiometricProfileResponse(BiometricProfileBase):
    student_id: str
    has_template: bool = False
    updated_at: str

class EmbeddingVariantCreate(BaseModel):
    embedding: List[float] = Field(..., description="512-dimensional normalized embedding vector")
    face_width: Optional[float] = Field(None, description="Face crop width in pixels")
    blur_score: Optional[float] = Field(None, description="Laplacian blur variance")
    illumination_score: Optional[float] = Field(None, description="Illumination contrast / lux percentage")
    yaw: Optional[float] = Field(None, description="Pose yaw angle in degrees (-90 to +90)")
    pitch: Optional[float] = Field(None, description="Pose pitch angle in degrees (-90 to +90)")
    roll: Optional[float] = Field(None, description="Pose roll angle in degrees (-90 to +90)")
    detection_confidence: Optional[float] = Field(None, description="Face detector confidence score (0 to 1)")
    quality_score: float = Field(0.0, description="Composite enrollment quality metric (0 to 1)")
    source_image: Optional[str] = Field(None, description="Path or reference URI to source image crop")

class EmbeddingVariantResponse(BaseModel):
    id: int
    student_id: str
    face_width: Optional[float] = None
    blur_score: Optional[float] = None
    illumination_score: Optional[float] = None
    yaw: Optional[float] = None
    pitch: Optional[float] = None
    roll: Optional[float] = None
    detection_confidence: Optional[float] = None
    quality_score: float = 0.0
    source_image: Optional[str] = None
    created_at: str

class StudentDetailResponse(StudentResponse):
    biometric_profile: Optional[BiometricProfileResponse] = None
    variants: List[EmbeddingVariantResponse] = []

def serialize_embedding(embedding: Union[np.ndarray, List[float]]) -> bytes:
    """Serializes a 512-D float32 vector to raw binary bytes."""
    arr = np.array(embedding, dtype=np.float32)
    return arr.tobytes()

def deserialize_embedding(raw_bytes: bytes) -> List[float]:
    """Deserializes raw binary bytes back to a list of floats."""
    if not raw_bytes:
        return []
    arr = np.frombuffer(raw_bytes, dtype=np.float32)
    return arr.tolist()
