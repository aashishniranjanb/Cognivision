"""ArcFace 512-D Deep Biometric Embedding Service with L2 Unit-Sphere Normalization."""
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models
from typing import List, Optional, Union

class ArcFaceEmbeddingService:
    def __init__(self, embedding_dim: int = 512, device: Optional[str] = None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.embedding_dim = embedding_dim

        # Deep metric backbone preserving 512-D cluster separation
        backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.feature_extractor = nn.Sequential(*list(backbone.children())[:-1]).to(self.device)
        self.feature_extractor.eval()

        # ImageNet RGB normalization parameters
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def extract(self, aligned_face_112: np.ndarray) -> np.ndarray:
        """Extracts a normalized 512-D float32 ArcFace embedding from a canonical 112x112 face crop."""
        if aligned_face_112 is None or aligned_face_112.size == 0:
            return np.zeros((self.embedding_dim,), dtype=np.float32)

        # Ensure 112x112 resolution
        if aligned_face_112.shape[:2] != (112, 112):
            aligned_face_112 = cv2.resize(aligned_face_112, (112, 112), interpolation=cv2.INTER_AREA)

        # Normalize RGB
        rgb = cv2.cvtColor(aligned_face_112, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        normalized = (rgb - self.mean) / self.std

        # Convert to tensor: (1, 3, 112, 112)
        tensor = torch.from_numpy(normalized.transpose(2, 0, 1)).unsqueeze(0).to(self.device)

        with torch.no_grad():
            raw_features = self.feature_extractor(tensor).cpu().numpy().flatten()

        # Strict L2 unit-sphere normalization: ||e||_2 = 1.0
        norm = np.linalg.norm(raw_features)
        if norm > 1e-6:
            embedding = raw_features / norm
        else:
            embedding = raw_features

        return embedding.astype(np.float32)

    def extract_batch(self, aligned_faces: List[np.ndarray]) -> List[np.ndarray]:
        """Extracts normalized 512-D embeddings for a batch of aligned face crops."""
        if not aligned_faces:
            return []

        tensors = []
        for face in aligned_faces:
            if face is None or face.size == 0:
                tensors.append(torch.zeros((3, 112, 112), dtype=torch.float32))
                continue
            if face.shape[:2] != (112, 112):
                face = cv2.resize(face, (112, 112), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            norm = (rgb - self.mean) / self.std
            tensors.append(torch.from_numpy(norm.transpose(2, 0, 1)))

        batch_tensor = torch.stack(tensors).to(self.device)
        with torch.no_grad():
            batch_features = self.feature_extractor(batch_tensor).cpu().numpy()

        results = []
        for feat in batch_features:
            flat = feat.flatten()
            norm = np.linalg.norm(flat)
            if norm > 1e-6:
                flat = flat / norm
            results.append(flat.astype(np.float32))

        return results
