"""
SCRIPT DI CHUYỂN DỮ LIỆU CŨ SANG CẤU TRÚC THƯ MỤC MỚI
Chạy 1 lần duy nhất để chuyển ảnh phẳng:
    database/MSSV_0.jpg, MSSV_1.jpg, ...
    → database/MSSV/0.jpg, database/MSSV/1.jpg, ...
"""

import os
import shutil
import glob

DATABASE_DIR = "database"

print("=" * 60)
print("  🔄 SCRIPT DI CHUYỂN DỮ LIỆU SANG CẤU TRÚC MỚI")
print("=" * 60)

# Tìm tất cả ảnh phẳng ở root database/
flat_images = glob.glob(os.path.join(DATABASE_DIR, "*.jpg")) + \
              glob.glob(os.path.join(DATABASE_DIR, "*.png"))

if len(flat_images) == 0:
    print("\n[INFO] Không tìm thấy ảnh phẳng nào ở root database/.")
    print("       Dữ liệu đã ở cấu trúc mới hoặc chưa có dữ liệu.")
    exit()

print(f"\n[INFO] Tìm thấy {len(flat_images)} ảnh phẳng cần di chuyển.\n")

# Phân loại ảnh theo MSSV
migration_map = {}  # {MSSV: [(old_path, new_filename), ...]}

for image_path in flat_images:
    basename = os.path.basename(image_path)
    file_name_no_ext = os.path.splitext(basename)[0]
    ext = os.path.splitext(basename)[1]

    # Bóc tách: "22D14801030074_12.jpg" → ma_sv = "22D14801030074", idx = "12"
    if '_' in file_name_no_ext:
        parts = file_name_no_ext.split('_', 1)
        ma_sv = parts[0]
        idx = parts[1]
        new_filename = f"{idx}{ext}"
    else:
        # Ảnh không có underscore: "22D14801030074.jpg" → giữ nguyên tên
        ma_sv = file_name_no_ext
        new_filename = f"0{ext}"

    if ma_sv not in migration_map:
        migration_map[ma_sv] = []
    migration_map[ma_sv].append((image_path, new_filename))

# Thực hiện di chuyển
total_moved = 0
for ma_sv, files in migration_map.items():
    student_dir = os.path.join(DATABASE_DIR, ma_sv)
    if not os.path.exists(student_dir):
        os.makedirs(student_dir)

    print(f"  📂 {ma_sv}/ ({len(files)} ảnh)")
    for old_path, new_filename in files:
        new_path = os.path.join(student_dir, new_filename)
        shutil.move(old_path, new_path)
        total_moved += 1

print(f"\n{'═' * 60}")
print(f"  ✅ HOÀN TẤT DI CHUYỂN!")
print(f"     Đã di chuyển {total_moved} ảnh của {len(migration_map)} sinh viên.")
print(f"")
print(f"  📂 Cấu trúc mới:")
for ma_sv in migration_map:
    student_dir = os.path.join(DATABASE_DIR, ma_sv)
    file_count = len(os.listdir(student_dir))
    print(f"     └── {ma_sv}/ ({file_count} ảnh)")
print(f"")
print(f"  👉 BƯỚC TIẾP THEO:")
print(f"     Chạy '02_face_training.py' để huấn luyện lại AI!")
print(f"{'═' * 60}")
