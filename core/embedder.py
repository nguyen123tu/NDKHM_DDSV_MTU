"""
Core AI: Trích xuất Face Embedding Vector (512 chiều).
Dùng InsightFace buffalo_l model. Singleton pattern.
"""

import cv2
import numpy as np
from insightface.app import FaceAnalysis

# Singleton instance
_instance = None


class FaceEmbedder:
    """
    Trích xuất embedding vector 512 chiều từ khuôn mặt.
    
    Embedding vector là "dấu vân tay số" của khuôn mặt,
    dùng để so sánh 2 khuôn mặt có giống nhau không.
    """

    def __init__(self):
        """Khởi tạo InsightFace model cho embedding extraction."""
        print("[AI] Đang tải FaceEmbedder (buffalo_l)...")
        self._app = FaceAnalysis(
            name='buffalo_l',
            providers=['CPUExecutionProvider']
        )
        self._app.prepare(ctx_id=0, det_size=(640, 640))
        print("[AI] FaceEmbedder đã sẵn sàng.")

    def embed(self, frame):
        """
        Trích xuất embedding từ frame chứa khuôn mặt.
        
        Args:
            frame: numpy array BGR từ OpenCV
            
        Returns:
            numpy array: Embedding vector 512 chiều (L2 normalized),
                         hoặc None nếu không tìm thấy khuôn mặt.
        """
        if frame is None:
            return None

        faces = self._app.get(frame)
        if len(faces) == 0:
            return None

        # Lấy khuôn mặt lớn nhất (gần camera nhất)
        embedding = faces[0].embedding
        # L2 Normalize để chuẩn hóa vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def embed_from_file(self, image_path):
        """
        Trích xuất embedding từ file ảnh.
        
        Args:
            image_path: Đường dẫn tới file ảnh (jpg/png)
            
        Returns:
            numpy array hoặc None
        """
        img = cv2.imread(image_path)
        if img is None:
            print(f"[AI CẢNH BÁO] Không đọc được file: {image_path}")
            return None
        return self.embed(img)

    def embed_multiple(self, frame):
        """
        Trích xuất embedding cho TẤT CẢ khuôn mặt trong frame.
        
        Args:
            frame: numpy array BGR
            
        Returns:
            list: [(face_object, embedding_normalized), ...]
        """
        if frame is None:
            return []

        faces = self._app.get(frame)
        results = []
        for face in faces:
            emb = face.embedding
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            results.append((face, emb))
        return results


def get_embedder():
    """Lấy singleton instance của FaceEmbedder."""
    global _instance
    if _instance is None:
        _instance = FaceEmbedder()
    return _instance


if __name__ == '__main__':
    # Test: Trích xuất embedding từ webcam
    print("=== TEST FACE EMBEDDER ===")
    embedder = get_embedder()
    cap = cv2.VideoCapture(0)

    ret, frame = cap.read()
    if ret:
        emb = embedder.embed(frame)
        if emb is not None:
            print(f"Embedding shape: {emb.shape}")
            print(f"Embedding norm: {np.linalg.norm(emb):.4f}")
            print(f"First 5 values: {emb[:5]}")
        else:
            print("Không phát hiện khuôn mặt trong frame.")
    
    cap.release()
