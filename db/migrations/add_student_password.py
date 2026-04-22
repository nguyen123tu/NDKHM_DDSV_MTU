import sys
import os

# Thêm đường dẫn gốc vào sys.path để có thể import từ db và config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db.connection import execute_update, execute_query
from werkzeug.security import generate_password_hash

def run_migration():
    print("[MIGRATION] Bắt đầu quá trình cập nhật cấu trúc bảng sinh_vien...")
    
    # 1. Thêm cột password_hash vào bảng sinh_vien
    try:
        sql_alter = "ALTER TABLE sinh_vien ADD COLUMN password_hash VARCHAR(255) AFTER mssv;"
        execute_update(sql_alter)
        print("[OK] Đã thêm cột password_hash vào bảng sinh_vien.")
    except Exception as e:
        # Nếu cột đã tồn tại thì sẽ bắn exception, bỏ qua
        print(f"[INFO] Cột password_hash có thể đã tồn tại: {e}")
        
    # 2. Lấy danh sách toàn bộ sinh viên
    print("[MIGRATION] Đang cấp mật khẩu mặc định (MSSV) cho sinh viên...")
    students = execute_query("SELECT id, mssv FROM sinh_vien WHERE password_hash IS NULL")
    
    if not students:
        print("[INFO] Tất cả sinh viên đã có mật khẩu, không cần cập nhật.")
        return
        
    count = 0
    for sv in students:
        sv_id = sv['id']
        mssv = sv['mssv']
        
        # Mật khẩu mặc định bằng MSSV
        default_pwd = mssv
        pwd_hash = generate_password_hash(default_pwd, method='pbkdf2:sha256')
        
        execute_update("UPDATE sinh_vien SET password_hash = %s WHERE id = %s", (pwd_hash, sv_id))
        count += 1
        print(f"  -> Đã cấp mật khẩu cho MSSV: {mssv}")
        
    print(f"[HOÀN TẤT] Đã cập nhật thành công mật khẩu cho {count} sinh viên.")

if __name__ == '__main__':
    run_migration()
