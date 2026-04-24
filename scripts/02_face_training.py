"""
BƯỚC 2: CÔNG CỤ HUẤN LUYỆN (AVERAGE EMBEDDINGS)
Quét toàn bộ thư mục con trong database/ (mỗi thư mục = 1 sinh viên),
trích xuất tất cả Vectors và LẤY TRUNG BÌNH CỘNG lại thành 1 Vector siêu mạnh duy nhất.

CẤU TRÚC ĐỌC:
    database/
    ├── MSSV_1/         ← Tên thư mục = Mã sinh viên
    │   ├── 0.jpg
    │   ├── 1.jpg
    │   └── ...
    ├── MSSV_2/
    │   └── ...
    └── (ảnh phẳng cũ vẫn đọc được: MSSV_0.jpg, ...)
"""

import os
import glob
import cv2
import pickle
import time
import numpy as np
from insightface.app import FaceAnalysis

DATABASE_DIR = "database"
MODELS_DIR = "models"
EMBEDDINGS_FILE = os.path.join(MODELS_DIR, "embeddings.pkl")

if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

print("=" * 60)
print("BƯỚC 2: HUẤN LUYỆN LỚP NHẬN DIỆN (Multi-Angle Average)")
print("       📂 Quét thư mục con: database/<MSSV>/*.jpg")
print("=" * 60)

print("\n[1] Đang tải Trọng số Neural Network (InsightFace)...")
app_face = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app_face.prepare(ctx_id=0, det_size=(640, 640))

print("\n[2] Bắt đầu duyệt toàn bộ thư viện Ảnh...")

# Biến tạm chứa List các vector của mỗi người
embeddings_dict = {}
success_images = 0
start_time = time.time()

# ===== PHẦN 1: Quét các THƯ MỤC CON (cấu trúc mới) =====
subdirs = [d for d in os.listdir(DATABASE_DIR)
           if os.path.isdir(os.path.join(DATABASE_DIR, d))]

print(f"\n   📁 Tìm thấy {len(subdirs)} thư mục sinh viên.")

for ma_sv_dir in subdirs:
    student_path = os.path.join(DATABASE_DIR, ma_sv_dir)
    image_files = glob.glob(os.path.join(student_path, "*.jpg")) + \
                  glob.glob(os.path.join(student_path, "*.png"))

    if len(image_files) == 0:
        print(f"   [⚠] Thư mục '{ma_sv_dir}': Không có ảnh, bỏ qua.")
        continue

    print(f"   [📷] Thư mục '{ma_sv_dir}': Đang xử lý {len(image_files)} ảnh...", end=" ")
    count_ok = 0

    for image_path in image_files:
        img = cv2.imread(image_path)
        if img is None:
            continue

        faces = app_face.get(img)
        if len(faces) > 0:
            if ma_sv_dir not in embeddings_dict:
                embeddings_dict[ma_sv_dir] = []
            embeddings_dict[ma_sv_dir].append(faces[0].embedding)
            success_images += 1
            count_ok += 1

    print(f"✅ {count_ok}/{len(image_files)} ảnh nhận diện được khuôn mặt.")

# ===== PHẦN 2: Fallback - Quét ảnh phẳng cũ ở root database/ (tương thích ngược) =====
flat_images = glob.glob(os.path.join(DATABASE_DIR, "*.jpg")) + \
              glob.glob(os.path.join(DATABASE_DIR, "*.png"))

if len(flat_images) > 0:
    print(f"\n   📄 Tìm thấy {len(flat_images)} ảnh phẳng (cấu trúc cũ) ở root database/.")
    print(f"      💡 Gợi ý: Chạy 'migrate_old_database.py' để chuyển sang cấu trúc mới!")

    for image_path in flat_images:
        basename = os.path.basename(image_path)
        file_name_no_ext = os.path.splitext(basename)[0]

        # Bóc tách tên. Ví dụ "1234_12.jpg" -> ma_sv = "1234". Còn "1234.jpg" -> "1234"
        if '_' in file_name_no_ext:
            ma_sv = file_name_no_ext.split('_')[0]
        else:
            ma_sv = file_name_no_ext

        img = cv2.imread(image_path)
        if img is None:
            continue

        faces = app_face.get(img)
        if len(faces) > 0:
            if ma_sv not in embeddings_dict:
                embeddings_dict[ma_sv] = []
            embeddings_dict[ma_sv].append(faces[0].embedding)
            success_images += 1

print(f"\n[INFO] Đã xử lý thành công {success_images} bức ảnh của {len(embeddings_dict)} sinh viên.")

print("\n[3] Bắt đầu Tính toán Vector Trung Bình Tổng Hợp...")
known_faces = {}
for ma_sv, emb_list in embeddings_dict.items():
    if len(emb_list) == 1:
        # Nếu chỉ có 1 ảnh (ví dụ nạp từ Web) thì xài luôn
        known_faces[ma_sv] = emb_list[0]
        print(f"  [OK] Sinh viên {ma_sv}: Dùng góc độ đơn lẻ ({len(emb_list)} ảnh).")
    else:
        # Nếu có hàng chục ảnh (chụp từ Cam 50 góc): Tính Trung Bình Cấp Lũy Tiến
        avg_emb = np.mean(emb_list, axis=0)  # Cộng 50 lớp lại chia trung bình
        avg_emb = avg_emb / np.linalg.norm(avg_emb)  # L2 Norm chuẩn hóa
        known_faces[ma_sv] = avg_emb
        print(f"  [OK] Sinh viên {ma_sv}: Tạo siêu não bộ từ TỔNG HỢP {len(emb_list)} góc độ khác nhau.")

# 4. Ghi đè file models
if len(known_faces) > 0:
    with open(EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump(known_faces, f)

    calc_time = round(time.time() - start_time, 2)
    print(f"\n{'═' * 60}")
    print(f"  ✅ HOÀN TẤT HUẤN LUYỆN!")
    print(f"     Tổng: {len(known_faces)} sinh viên | Thời gian: {calc_time}s")
    print(f"     Não bộ AI đã lưu vào: {EMBEDDINGS_FILE}")
    print(f"")
    print(f"  👉 BƯỚC TIẾP THEO:")
    print(f"     Chạy file '03_face_recognition.py' để bắt đầu điểm danh!")
    print(f"{'═' * 60}")
else:
    print("\n[THẤT BẠI] Không có dữ liệu nào để huấn luyện.")
    print("           Hãy chạy '01_face_dataset.py' để chụp ảnh sinh viên trước!")
