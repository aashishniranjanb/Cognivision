"""V1.3 Biometrics Package — Schema, Database, Repository, and Migration."""
from app.biometrics.database import BiometricDatabase
from app.biometrics.schemas import (
    StudentCreate, StudentUpdate, StudentResponse,
    BiometricProfileBase, BiometricProfileResponse,
    EmbeddingVariantCreate, EmbeddingVariantResponse,
    StudentDetailResponse, serialize_embedding, deserialize_embedding
)
from app.biometrics.repository import BiometricRepository
from app.biometrics.migration import run_migration

__all__ = [
    "BiometricDatabase",
    "BiometricRepository",
    "StudentCreate",
    "StudentUpdate",
    "StudentResponse",
    "BiometricProfileBase",
    "BiometricProfileResponse",
    "EmbeddingVariantCreate",
    "EmbeddingVariantResponse",
    "StudentDetailResponse",
    "serialize_embedding",
    "deserialize_embedding",
    "run_migration"
]
