"""Body Re-ID Feature Extractor generating 512-d L2-normalized appearance embeddings."""
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models

class BodyEmbedder:
    def __init__(self, embedding_dim: int = 512, device: str = "cpu"):
        self.device = torch.device(device)
        self.embedding_dim = embedding_dim
        
        # Pretrained ResNet-18 feature extractor configured for 256x128 full-body Re-ID crops
        backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        self.feature_extractor = nn.Sequential(*list(backbone.children())[:-1]).to(self.device)
        self.feature_extractor.eval()

        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def extract(self, person_crop: np.ndarray) -> np.ndarray:
        """Extracts normalized 512-d appearance embedding from a full-body person crop."""
        if person_crop is None or person_crop.size == 0:
            return np.zeros((self.embedding_dim,), dtype=np.float32)

        # Standard Re-ID dimensions: 256 height x 128 width
        resized = cv2.resize(person_crop, (128, 256))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        norm = (rgb - self.mean) / self.std

        tensor = torch.from_numpy(norm.transpose(2, 0, 1)).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self.feature_extractor(tensor).cpu().numpy().flatten()

        norm_val = np.linalg.norm(features)
        if norm_val > 1e-6:
            features = features / norm_val
        return features.astype(np.float32)
