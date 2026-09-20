"""Face Embedding Extractor producing 512-dimensional L2-normalized identity representations."""
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models

class FaceEmbedder:
    def __init__(self, embedding_dim: int = 512, device: str = "cpu"):
        self.device = torch.device(device)
        self.embedding_dim = embedding_dim
        print(f"[FaceEmbedder] Initializing 512-d Face Embedding Extractor on {device}...")
        
        # Lightweight MobileNetV3-Small backbone with a 512-d feature projection head
        backbone = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        in_features = backbone.classifier[0].in_features
        backbone.classifier = nn.Sequential(
            nn.Linear(in_features, embedding_dim),
            nn.BatchNorm1d(embedding_dim)
        )
        self.model = backbone.to(self.device)
        self.model.eval()

        # Mean and std for input normalization
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def extract(self, face_crop: np.ndarray) -> np.ndarray:
        """Extracts 512-d unit-normalized embedding vector from a BGR face crop."""
        if face_crop is None or face_crop.size == 0:
            return np.zeros((self.embedding_dim,), dtype=np.float32)

        # Standard face alignment size (112x112)
        resized = cv2.resize(face_crop, (112, 112))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        norm = (rgb - self.mean) / self.std

        # Convert to Tensor (1, 3, 112, 112)
        tensor = torch.from_numpy(norm.transpose(2, 0, 1)).unsqueeze(0).to(self.device)

        with torch.no_grad():
            emb = self.model(tensor).cpu().numpy().flatten()

        # L2-normalization for cosine similarity via inner product
        norm_val = np.linalg.norm(emb)
        if norm_val > 1e-6:
            emb = emb / norm_val
        return emb.astype(np.float32)
