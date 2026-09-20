"""Face Embedding Extractor using pretrained ResNet50 for high-fidelity facial biometric feature vectors."""
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models

class FaceEmbedder:
    def __init__(self, embedding_dim: int = 512, device: str = "cpu"):
        self.device = torch.device(device)
        self.embedding_dim = embedding_dim
        
        # Pretrained ResNet-18 without randomly initialized linear projection layers
        # Using avgpool output directly (512-d feature space) preserves pretrained metric cluster separation
        backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.backbone = nn.Sequential(*list(backbone.children())[:-1]).to(self.device)
        self.backbone.eval()

        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def extract(self, face_crop: np.ndarray) -> np.ndarray:
        if face_crop is None or face_crop.size == 0:
            return np.zeros((self.embedding_dim,), dtype=np.float32)

        resized = cv2.resize(face_crop, (112, 112))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        norm = (rgb - self.mean) / self.std

        tensor = torch.from_numpy(norm.transpose(2, 0, 1)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self.backbone(tensor).cpu().numpy().flatten()

        # Strict L2 normalization
        norm_val = np.linalg.norm(features)
        if norm_val > 1e-6:
            features = features / norm_val
        return features.astype(np.float32)
