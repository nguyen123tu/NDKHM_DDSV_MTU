import os
import sys

# Đảm bảo import được các thư mục con
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.connection import init_database, seed_database
from config import Config

def main():
    print("="*60)
    print("🚀 KHỞI TẠO HỆ THỐNG ĐIỂM DANH COMPREHENSIVE V2")
    print("="*60)

    try:
        # Lấy thông số từ Config
        print(f"\n[1] Đang thiết lập Cơ sở dữ liệu: {Config.DB_NAME} (User: {Config.DB_USER})")
        
        # 1. Tạo CSDL và các bảng
        init_database()
        
        # 2. Xóa và nạp lại dữ liệu mẫu nếu cần
        print("\n[2] Nạp dữ liệu mẫu (Admin, Lớp học, Sinh viên)...")
        seed_database()
        
        # 3. Tạo thư mục cơ bản
        print("\n[3] Tạo các thư mục vật lý...")
        Config.init_dirs()
        print(f"  - Thư mục database: {Config.DATABASE_DIR} (OK)")
        print(f"  - Thư mục models: {Config.MODELS_DIR} (OK)")

        print("\n" + "="*60)
        print("🎉 HOÀN TẤT THIẾT LẬP HỆ THỐNG!")
        print("="*60)
        print("Tài khoản mặc định:")
        print("  - Username: admin")
        print("  - Password: admin123")
        print("\nĐể chạy máy chủ web, bạn hãy gõ lệnh:")
        print("  python app.py")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Lỗi khởi tạo: {e}")
        print("Hãy kiểm tra lại thông tin cài đặt MySQL trong file .env")

if __name__ == '__main__':
    main()
