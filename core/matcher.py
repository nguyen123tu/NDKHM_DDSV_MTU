"""
Core AI: So khớp khuôn mặt (Cosine Similarity).
Load embeddings.pkl vào RAM, so sánh realtime.
Thread-safe với threading.Lock.
"""

import os
import pickle
import threading
import numpy as np
from config import Config

# Singleton instance
_instance = None


class FaceMatcher:
    """
    So khớp embedding với cơ sở dữ liệu vector đã train.
    
    Đọc file embeddings.pkl (được tạo bởi FaceTrainer),
    lưu vào RAM để so sánh cực nhanh trong realtime.
    Tự động reload khi file pkl được cập nhật.
    """

    def __init__(self, pkl_path=None):
        """
        Args:
            pkl_path: Đường dẫn tới file embeddings.pkl
        """
        if pkl_path is None:
            if Config.AI_ENGINE == 'yolo_resnet':
                pkl_path = Config.EMBEDDINGS_YOLO_PATH
            elif Config.AI_ENGINE == 'deepface':
                pkl_path = Config.EMBEDDINGS_DEEPFACE_PATH
            else:
                pkl_path = Config.EMBEDDINGS_PATH
        self._pkl_path = pkl_path
        self._known_faces = {}       # {mssv: embedding_vector}
        self._last_mtime = 0         # Thời gian chỉnh sửa file pkl lần cuối
        self._lock = threading.Lock()  # Thread-safe
        self.load_brain()

    def load_brain(self):
        """Đọc file embeddings.pkl vào RAM."""
        if not os.path.exists(self._pkl_path):
            print(f"[AI MATCHER] Chưa tìm thấy file não bộ: {self._pkl_path}")
            return False

        try:
            with self._lock:
                with open(self._pkl_path, 'rb') as f:
                    self._known_faces = pickle.load(f)
                self._last_mtime = os.path.getmtime(self._pkl_path)
            print(f"[AI MATCHER] Đã nạp {len(self._known_faces)} vector não bộ.")
            return True
        except Exception as e:
            print(f"[AI MATCHER LỖI] Không đọc được pkl: {e}")
            return False

    def reload_if_updated(self):
        """
        Kiểm tra file pkl có được cập nhật không.
        Nếu có → tự động reload vào RAM (hot-reload).
        Nên gọi hàm này mỗi 10 giây trong vòng lặp chính.
        """
        if not os.path.exists(self._pkl_path):
            return False

        current_mtime = os.path.getmtime(self._pkl_path)
        if current_mtime > self._last_mtime:
            print("[AI MATCHER] Phát hiện não bộ mới! Đang reload...")
            return self.load_brain()
        return False

    def match(self, embedding, threshold=None):
        """
        So khớp embedding với cơ sở dữ liệu.
        
        Args:
            embedding: numpy array 512 chiều (đã L2 normalized)
            threshold: Ngưỡng similarity tối thiểu (mặc định từ Config)
            
        Returns:
            tuple: (mssv, similarity) nếu tìm thấy,
                   ("UNKNOWN", 0.0) nếu không khớp
        """
        if threshold is None:
            threshold = Config.SIMILARITY_THRESHOLD

        best_match = "UNKNOWN"
        best_sim = 0.0

        with self._lock:
            for mssv, known_emb in self._known_faces.items():
                # Cosine Similarity = dot(a, b) / (||a|| * ||b||)
                sim = np.dot(embedding, known_emb) / (
                    np.linalg.norm(embedding) * np.linalg.norm(known_emb)
                )
                if sim > best_sim and sim > threshold:
                    best_sim = float(sim)
                    best_match = mssv

        return best_match, best_sim

    def get_all_ids(self):
        """Lấy danh sách tất cả MSSV đã có trong não bộ."""
        with self._lock:
            return list(self._known_faces.keys())

    @property
    def total_faces(self):
        """Tổng số sinh viên đã train."""
        with self._lock:
            return len(self._known_faces)


def get_matcher(pkl_path=None):
    """Lấy singleton instance của FaceMatcher."""
    global _instance
    if _instance is None:
        _instance = FaceMatcher(pkl_path)
    return _instance


if __name__ == '__main__':
    # Test: Load và kiểm tra
    print("=== TEST FACE MATCHER ===")
    matcher = get_matcher()
    print(f"Tổng sinh viên đã train: {matcher.total_faces}")
    print(f"Danh sách MSSV: {matcher.get_all_ids()}")
