"""
Core AI: Huấn luyện (Training) — Tạo file embeddings.pkl.
Quét thư mục database/, trích xuất embedding average cho mỗi sinh viên.
Hỗ trợ cả cấu trúc thư mục con (MSSV/0.jpg) và phẳng (MSSV_0.jpg).
Hỗ trợ cả InsightFace và YOLOv8+ResNet50 engine.
"""

import os
import glob
import pickle
import time
import threading
import cv2
import numpy as np
from config import Config


class FaceTrainer:
    """
    Huấn luyện AI: Quét ảnh → trích xuất embedding → tính trung bình → lưu pkl.
    
    Quy trình:
    1. Duyệt từng thư mục con trong database/ (mỗi thư mục = 1 sinh viên)
    2. Đọc tất cả ảnh .jpg/.png bên trong
    3. Trích xuất embedding cho mỗi ảnh (engine-agnostic)
    4. Tính Average Embedding (trung bình cộng tất cả góc độ)
    5. L2 normalize vector trung bình
    6. Lưu vào file embeddings.pkl: {mssv: avg_embedding}
    """

    def __init__(self):
        """Khởi tạo trainer."""
        self._engine = None
        self._progress = 0.0           # % tiến độ (0.0 → 1.0)
        self._status = "idle"         # idle / training / done / error
        self._lock = threading.Lock()

    def _ensure_model(self):
        """Lazy load AI engine — chỉ tải khi thực sự cần."""
        if self._engine is None:
            from core.engine import get_engine
            print(f"[TRAINER] Đang tải AI engine ({Config.AI_ENGINE})...")
            self._engine = get_engine()
            print(f"[TRAINER] Engine đã sẵn sàng: {self._engine['name']}")

    def train_all(self, database_dir=None, output_pkl=None):
        """
        Quét toàn bộ database/ và tạo embeddings.pkl.
        
        Args:
            database_dir: Thư mục chứa ảnh (mặc định: Config.DATABASE_DIR)
            output_pkl: Đường dẫn file output (mặc định: Config.EMBEDDINGS_PATH)
            
        Returns:
            dict: {mssv: avg_embedding} — kết quả training
        """
        database_dir = database_dir or Config.DATABASE_DIR
        if output_pkl is None:
            output_pkl = Config.EMBEDDINGS_YOLO_PATH if Config.AI_ENGINE == 'yolo_resnet' else Config.EMBEDDINGS_PATH

        self._ensure_model()
        self._status = "training"
        self._progress = 0.0

        embeddings_dict = {}  # {mssv: [emb1, emb2, ...]}
        success_images = 0
        start_time = time.time()

        # === PHẦN 1: Quét thư mục con (cấu trúc mới) ===
        subdirs = []
        if os.path.exists(database_dir):
            subdirs = [d for d in os.listdir(database_dir)
                       if os.path.isdir(os.path.join(database_dir, d))]

        # Đếm tổng items để tính progress
        total_items = len(subdirs)
        
        # Đếm thêm ảnh phẳng
        flat_images = glob.glob(os.path.join(database_dir, "*.jpg")) + \
                      glob.glob(os.path.join(database_dir, "*.png"))
        total_items += len(flat_images)

        if total_items == 0:
            self._status = "error"
            print("[TRAINER] Không tìm thấy dữ liệu nào trong database/")
            return {}

        processed = 0

        for ma_sv_dir in subdirs:
            student_path = os.path.join(database_dir, ma_sv_dir)
            image_files = glob.glob(os.path.join(student_path, "*.jpg")) + \
                          glob.glob(os.path.join(student_path, "*.png"))

            if len(image_files) == 0:
                processed += 1
                self._progress = processed / total_items
                continue

            count_ok = 0
            for image_path in image_files:
                # Fix unicode path for Windows
                img_data = np.fromfile(image_path, np.uint8)
                if img_data is None or len(img_data) == 0:
                    continue
                img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)

                if img is None:
                    continue
                face_results = self._engine['detect_and_embed'](img)
                if len(face_results) > 0:
                    emb = face_results[0]['embedding']
                    norm = np.linalg.norm(emb)
                    if norm > 0:
                        emb = emb / norm
                    if ma_sv_dir not in embeddings_dict:
                        embeddings_dict[ma_sv_dir] = []
                    embeddings_dict[ma_sv_dir].append(emb)
                    success_images += 1
                    count_ok += 1

            processed += 1
            self._progress = processed / total_items
            print(f"  [TRAINER] {ma_sv_dir}: {count_ok}/{len(image_files)} ảnh OK")

        # === PHẦN 2: Fallback ảnh phẳng (cấu trúc cũ) ===
        for image_path in flat_images:
            basename = os.path.basename(image_path)
            file_name_no_ext = os.path.splitext(basename)[0]

            if '_' in file_name_no_ext:
                ma_sv = file_name_no_ext.split('_')[0]
            else:
                ma_sv = file_name_no_ext

            # Fix unicode path for Windows
            img_data = np.fromfile(image_path, np.uint8)
            img = cv2.imdecode(img_data, cv2.IMREAD_COLOR) if len(img_data) > 0 else None

            if img is not None:
                face_results = self._engine['detect_and_embed'](img)
                if len(face_results) > 0:
                    emb = face_results[0]['embedding']
                    norm = np.linalg.norm(emb)
                    if norm > 0:
                        emb = emb / norm
                    if ma_sv not in embeddings_dict:
                        embeddings_dict[ma_sv] = []
                    embeddings_dict[ma_sv].append(emb)
                    success_images += 1

            processed += 1
            self._progress = processed / total_items

        # === PHẦN 3: Tính Average Embedding ===
        known_faces = {}
        for ma_sv, emb_list in embeddings_dict.items():
            if len(emb_list) == 1:
                known_faces[ma_sv] = emb_list[0]
            else:
                avg_emb = np.mean(emb_list, axis=0)
                avg_emb = avg_emb / np.linalg.norm(avg_emb)  # L2 Normalize
                known_faces[ma_sv] = avg_emb
            print(f"  [TRAINER] {ma_sv}: Vector từ {len(emb_list)} góc độ")

        # === PHẦN 4: Lưu file pkl ===
        if len(known_faces) > 0:
            os.makedirs(os.path.dirname(output_pkl), exist_ok=True)
            with open(output_pkl, 'wb') as f:
                pickle.dump(known_faces, f)

            calc_time = round(time.time() - start_time, 2)
            self._status = "done"
            self._progress = 1.0
            print(f"\n[TRAINER] Hoàn tất! {len(known_faces)} sinh viên | {calc_time}s")
            return known_faces
        else:
            self._status = "error"
            print("[TRAINER] Không trích xuất được embedding nào!")
            return {}

    def train_one(self, mssv, image_paths=None, output_pkl=None):
        """
        Train/update chỉ 1 sinh viên cụ thể (không ảnh hưởng người khác).
        
        Args:
            mssv: Mã số sinh viên
            image_paths: List đường dẫn ảnh (nếu None → quét thư mục database/MSSV/)
            output_pkl: Đường dẫn pkl output
            
        Returns:
            bool: True nếu train thành công
        """
        database_dir = Config.DATABASE_DIR
        if output_pkl is None:
            output_pkl = Config.EMBEDDINGS_YOLO_PATH if Config.AI_ENGINE == 'yolo_resnet' else Config.EMBEDDINGS_PATH

        self._ensure_model()

        # Xác định danh sách ảnh
        if image_paths is None:
            student_dir = os.path.join(database_dir, mssv)
            if not os.path.exists(student_dir):
                print(f"[TRAINER] Không tìm thấy thư mục: {student_dir}")
                return False
            image_paths = glob.glob(os.path.join(student_dir, "*.jpg")) + \
                          glob.glob(os.path.join(student_dir, "*.png"))

        if len(image_paths) == 0:
            print(f"[TRAINER] Không có ảnh cho {mssv}")
            return False

        # Trích xuất embeddings
        emb_list = []
        for path in image_paths:
            img_data = np.fromfile(path, np.uint8)
            if img_data is None or len(img_data) == 0:
                continue
            img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)

            if img is None:
                continue
            face_results = self._engine['detect_and_embed'](img)
            if len(face_results) > 0:
                emb = face_results[0]['embedding']
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                emb_list.append(emb)

        if len(emb_list) == 0:
            return False

        # Tính average
        if len(emb_list) == 1:
            final_emb = emb_list[0]
        else:
            final_emb = np.mean(emb_list, axis=0)
            final_emb = final_emb / np.linalg.norm(final_emb)

        # Load pkl hiện tại, cập nhật, rồi lưu lại
        known_faces = {}
        if os.path.exists(output_pkl):
            with open(output_pkl, 'rb') as f:
                known_faces = pickle.load(f)

        known_faces[mssv] = final_emb

        os.makedirs(os.path.dirname(output_pkl), exist_ok=True)
        with open(output_pkl, 'wb') as f:
            pickle.dump(known_faces, f)

        print(f"[TRAINER] Đã train {mssv}: {len(emb_list)} ảnh → 1 vector")
        return True

    def get_progress(self):
        """
        Lấy tiến độ training hiện tại.
        
        Returns:
            dict: {"progress": 0.0-1.0, "status": "idle/training/done/error"}
        """
        return {
            "progress": self._progress,
            "status": self._status
        }


if __name__ == '__main__':
    # Test: Train toàn bộ database
    print("=== TEST FACE TRAINER ===")
    trainer = FaceTrainer()
    result = trainer.train_all()
    print(f"\nKết quả: {len(result)} sinh viên đã được train")
    for mssv, emb in result.items():
        print(f"  {mssv}: shape={emb.shape}, norm={np.linalg.norm(emb):.4f}")
