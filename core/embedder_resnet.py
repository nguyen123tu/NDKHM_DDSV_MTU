"""
Core AI: Trích xuất Face Embedding bằng ResNet50 (PyTorch).
Thay thế ArcFace (InsightFace) bằng ResNet50 pretrained trên ImageNet,
với lớp FC cuối được bỏ đi để lấy feature vector 2048 chiều.
Singleton pattern.
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms

# Singleton instance
_instance = None


class ResNet50Embedder:
    """
    Trích xuất embedding vector từ ảnh khuôn mặt bằng ResNet50.

    ResNet50 pretrained trên ImageNet được sử dụng như feature extractor.
    Bỏ lớp FC cuối cùng (1000 classes) → lấy output 2048 chiều.
    Vector được L2 normalize trước khi trả về.
    """

    def __init__(self):
        """Khởi tạo ResNet50 pretrained."""
        print("[RESNET] Đang tải ResNet50 pretrained...")

        # Load ResNet50 pretrained trên ImageNet
        self._model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)

        # Bỏ lớp FC cuối → output = 2048 chiều
        self._model = nn.Sequential(*list(self._model.children())[:-1])

        self._model.eval()  # Chế độ inference

        # Transform chuẩn ImageNet
        self._transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

        self._embedding_dim = 2048
        print(f"[RESNET] ResNet50 đã sẵn sàng (embedding_dim={self._embedding_dim})")

    @property
    def embedding_dim(self):
        return self._embedding_dim

    def embed(self, face_crop):
        """
        Trích xuất embedding từ ảnh khuôn mặt đã crop.

        Args:
            face_crop: numpy array BGR (ảnh khuôn mặt đã crop từ detector)

        Returns:
            numpy array: Embedding vector 2048 chiều (L2 normalized),
                         hoặc None nếu lỗi.
        """
        if face_crop is None or face_crop.size == 0:
            return None

        try:
            # BGR → RGB
            rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

            # Transform
            tensor = self._transform(rgb).unsqueeze(0)  # Thêm batch dimension

            # Forward pass
            with torch.no_grad():
                features = self._model(tensor)

            # Squeeze → numpy → L2 normalize
            embedding = features.squeeze().numpy()
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            return embedding

        except Exception as e:
            print(f"[RESNET LỖI] {e}")
            return None

    def embed_from_file(self, image_path):
        """
        Trích xuất embedding từ file ảnh.

        Args:
            image_path: Đường dẫn tới file ảnh

        Returns:
            numpy array hoặc None
        """
        img_data = np.fromfile(image_path, np.uint8)
        if img_data is None or len(img_data) == 0:
            return None
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        if img is None:
            return None
        return self.embed(img)


def get_resnet_embedder():
    """Lấy singleton instance của ResNet50Embedder."""
    global _instance
    if _instance is None:
        _instance = ResNet50Embedder()
    return _instance
