"""
Core AI: So khớp khuôn mặt (Cosine Similarity).
Load embeddings.pkl vào RAM, so sánh realtime.
Thread-safe với threading.Lock.
"""

import sys
import os
import pickle
import threading
import numpy as np
import numpy.core.numeric
import numpy.core.multiarray

# Patch cho numpy 1.x load file pkl từ numpy 2.x
sys.modules["numpy._core"] = sys.modules["numpy.core"]
sys.modules["numpy._core.numeric"] = sys.modules["numpy.core.numeric"]
sys.modules["numpy._core.multiarray"] = sys.modules["numpy.core.multiarray"]

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
            if Config.AI_ENGINE == "yolo_resnet":
                pkl_path = Config.EMBEDDINGS_YOLO_PATH
            elif Config.AI_ENGINE == "deepface":
                pkl_path = Config.EMBEDDINGS_DEEPFACE_PATH
            else:
                pkl_path = Config.EMBEDDINGS_PATH
        self._pkl_path = pkl_path
        self._known_faces = {}  # {mssv: embedding_vector}
        self._last_mtime = 0  # Thời gian chỉnh sửa file pkl lần cuối
        self._lock = threading.Lock()  # Thread-safe
        self.load_brain()

    def _get_active_model_path(self):
        if os.path.exists(self._pkl_path):
            return self._pkl_path
        legacy_path = self._pkl_path.replace(".npz", ".pkl")
        if os.path.exists(legacy_path):
            return legacy_path
        return self._pkl_path

    def load_brain(self):
        """Đọc file embeddings.npz (hoặc pkl legacy) vào RAM."""
        active_path = self._get_active_model_path()
        if not os.path.exists(active_path):
            print(f"[AI MATCHER] Chưa tìm thấy file não bộ: {active_path}")
            return False

        try:
            with self._lock:
                if active_path.endswith(".npz"):
                    data = np.load(active_path, allow_pickle=False)
                    keys = [str(k) for k in data["keys"]]
                    values = data["values"]
                    self._known_faces = {k: v for k, v in zip(keys, values)}
                else:
                    with open(active_path, "rb") as f:
                        self._known_faces = pickle.load(f)

                # Tối ưu hóa: Tạo Ma trận (N x 512) để so sánh song song hàng nghìn mặt
                if len(self._known_faces) > 0:
                    self._mssv_list = list(self._known_faces.keys())
                    emb_matrix = np.array(list(self._known_faces.values()))

                    # L2 Normalize ma trận một lần duy nhất lúc load
                    norms = np.linalg.norm(emb_matrix, axis=1, keepdims=True)
                    # Tránh chia cho 0
                    self._emb_matrix = np.where(
                        norms > 0, emb_matrix / norms, emb_matrix
                    )
                else:
                    self._mssv_list = []
                    self._emb_matrix = np.array([])

                self._last_mtime = os.path.getmtime(active_path)
            print(
                f"[AI MATCHER] Đã nạp {len(self._known_faces)} vector não bộ (Ma trận Tối ưu)."
            )
            return True
        except Exception as e:
            print(f"[AI MATCHER LỖI] Không đọc được file não bộ ({active_path}): {e}")
            return False

    def reload_if_updated(self):
        """
        Kiểm tra file model (.npz/.pkl) có được cập nhật không.
        Nếu có → tự động reload vào RAM (hot-reload).
        Nên gọi hàm này mỗi 10 giây trong vòng lặp chính.
        """
        active_path = self._get_active_model_path()
        if not os.path.exists(active_path):
            return False

        current_mtime = os.path.getmtime(active_path)
        if current_mtime > self._last_mtime:
            print("[AI MATCHER] Phát hiện não bộ mới! Đang reload...")
            return self.load_brain()
        return False

    def match(self, embedding, threshold=None):
        """
        So khớp embedding với cơ sở dữ liệu. Tốc độ siêu cao nhờ Matrix Multiplication.

        Args:
            embedding: numpy array 512 chiều
            threshold: Ngưỡng similarity tối thiểu

        Returns:
            tuple: (mssv, similarity)
        """
        if threshold is None:
            threshold = Config.SIMILARITY_THRESHOLD

        best_match = "UNKNOWN"
        best_sim = 0.0

        with self._lock:
            if len(self._mssv_list) == 0 or self._emb_matrix.size == 0:
                return best_match, best_sim

            # L2 Normalize input embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            # NHÂN MA TRẬN: So sánh 1 vector với TẤT CẢ sinh viên cùng lúc
            # Kết quả là mảng similarities chứa độ giống nhau với từng sinh viên
            similarities = np.dot(self._emb_matrix, embedding)

            # Lấy index của sinh viên giống nhất
            best_idx = np.argmax(similarities)
            best_sim = float(similarities[best_idx])

            if best_sim > threshold:
                best_match = self._mssv_list[best_idx]

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


if __name__ == "__main__":
    # Test: Load và kiểm tra
    print("=== TEST FACE MATCHER ===")
    matcher = get_matcher()
    print(f"Tổng sinh viên đã train: {matcher.total_faces}")
    print(f"Danh sách MSSV: {matcher.get_all_ids()}")
