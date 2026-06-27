"""
Service: Quản lý Sinh Viên.
Tất cả truy vấn DB liên quan tới bảng sinh_vien đều nằm ở đây.
"""

from db.connection import execute_query, execute_one, execute_update
import os
import glob
from config import Config

def get_avatar_path(mssv):
    """
    Trả về đường dẫn avatar của SV.
    Nếu trong DB không có hoặc không tồn tại file, tự động tìm file ảnh đầu tiên trong database/mssv/.
    """
    sv = execute_one("SELECT avatar FROM sinh_vien WHERE mssv = %s", (mssv,))
    avatar_path = sv.get('avatar') if sv else None
    
    if not avatar_path or not os.path.exists(os.path.join(Config.BASE_DIR, avatar_path)):
        # Tìm file trong dataset
        db_path = os.path.join(Config.DATABASE_DIR, mssv)
        images = glob.glob(f"{db_path}/*.jpg") + glob.glob(f"{db_path}/*.png")
        if images:
            avatar_path = f"database/{mssv}/{os.path.basename(images[0])}"
        else:
            avatar_path = None
            
    return avatar_path


def get_all(lop_id=None, search=None, page=1, per_page=20):
    """
    Lấy danh sách sinh viên có phân trang và filter.
    
    Args:
        lop_id: Lọc theo lớp (optional)
        search: Tìm kiếm theo tên hoặc MSSV (optional)
        page: Trang hiện tại (1-indexed)
        per_page: Số bản ghi mỗi trang
        
    Returns:
        dict: {"items": list, "total": int, "pages": int, "current": int}
    """
    conditions = ["sv.trang_thai = 1"]
    params = []

    if lop_id:
        conditions.append("sv.lop_id = %s")
        params.append(lop_id)

    if search:
        conditions.append("(sv.mssv LIKE %s OR sv.ho_ten LIKE %s)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    where_clause = " AND ".join(conditions)

    # Đếm tổng
    count_sql = f"SELECT COUNT(*) as total FROM sinh_vien sv WHERE {where_clause}"
    count_result = execute_one(count_sql, tuple(params) if params else None)
    total = count_result["total"] if count_result else 0

    # Tính phân trang
    pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    # Query dữ liệu + JOIN lấy tên lớp
    data_sql = f"""
        SELECT sv.*, lh.ten_lop, lh.ma_lop 
        FROM sinh_vien sv
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE {where_clause}
        ORDER BY created_at DESC
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    """
    params.extend([offset, per_page])
    items = execute_query(data_sql, tuple(params))

    return {
        "items": items,
        "total": total,
        "pages": pages,
        "current": page
    }


def get_by_id(student_id):
    """Lấy thông tin sinh viên theo ID (kèm tên lớp)."""
    sql = """
        SELECT sv.*, lh.ten_lop, lh.ma_lop
        FROM sinh_vien sv
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE sv.id = %s
    """
    return execute_one(sql, (student_id,))


def get_by_mssv(mssv):
    """Lấy thông tin sinh viên theo MSSV (kèm tên lớp)."""
    sql = """
        SELECT sv.*, lh.ten_lop, lh.ma_lop
        FROM sinh_vien sv
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE sv.mssv = %s
    """
    return execute_one(sql, (mssv,))


def get_name_by_mssv(mssv):
    """Lấy họ tên sinh viên (dùng nhanh trong nhận diện realtime)."""
    if mssv == "UNKNOWN":
        return "Kẻ Lạ"
    result = execute_one("SELECT ho_ten FROM sinh_vien WHERE mssv = %s", (mssv,))
    return result["ho_ten"] if result else mssv


def create(data):
    """
    Thêm sinh viên mới.
    
    Args:
        data: dict với keys: mssv, ho_ten, email, sdt, lop_id, avatar, ngay_sinh, gioi_tinh
        
    Returns:
        int: ID sinh viên mới, hoặc -1 nếu lỗi
    """
    from werkzeug.security import generate_password_hash
    
    sql = """
        INSERT INTO sinh_vien (mssv, password_hash, ho_ten, email, sdt, lop_id, avatar, ngay_sinh, gioi_tinh)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    default_pwd = data.get("mssv")
    pwd_hash = generate_password_hash(default_pwd, method='pbkdf2:sha256') if default_pwd else None
    
    params = (
        data.get("mssv"),
        pwd_hash,
        data.get("ho_ten"),
        data.get("email"),
        data.get("sdt"),
        data.get("lop_id"),
        data.get("avatar"),
        data.get("ngay_sinh"),
        data.get("gioi_tinh")
    )
    return execute_update(sql, params)


def update(student_id, data):
    """
    Cập nhật thông tin sinh viên.
    
    Args:
        student_id: ID sinh viên
        data: dict chứa các trường cần cập nhật
        
    Returns:
        bool: True nếu thành công
    """
    allowed_fields = ["ho_ten", "email", "sdt", "lop_id", "avatar", "ngay_sinh", "gioi_tinh", "da_train", "trang_thai", "trang_thai_face", "password_hash"]
    set_parts = []
    params = []

    for field in allowed_fields:
        if field in data:
            set_parts.append(f"{field} = %s")
            params.append(data[field])

    if not set_parts:
        return False

    params.append(student_id)
    sql = f"UPDATE sinh_vien SET {', '.join(set_parts)} WHERE id = %s"
    result = execute_update(sql, tuple(params))
    return result >= 0


def delete(student_id):
    """Xóa cứng sinh viên khỏi Database và xóa thư mục ảnh liên quan."""
    import shutil
    import os
    from config import Config
    
    sv = get_by_id(student_id)
    if not sv:
        return False
        
    mssv = sv['mssv']

    sql = "DELETE FROM sinh_vien WHERE id = %s"
    result = execute_update(sql, (student_id,))
    
    if result >= 0:
        student_dir = os.path.join(Config.DATABASE_DIR, mssv)
        if os.path.exists(student_dir):
            try:
                shutil.rmtree(student_dir)
            except Exception as e:
                print(f"Lỗi khi xóa thư mục ảnh của {mssv}: {e}")
        return True
    return False


def mark_trained(mssv):
    """Đánh dấu sinh viên đã được train AI (da_train = 1)."""
    sql = "UPDATE sinh_vien SET da_train = 1 WHERE mssv = %s"
    result = execute_update(sql, (mssv,))
    return result >= 0


def count_images(mssv):
    """Đếm số ảnh trong thư mục database/MSSV/."""
    import os
    import glob
    from config import Config

    student_dir = os.path.join(Config.DATABASE_DIR, mssv)
    if not os.path.exists(student_dir):
        return 0
    jpg_files = glob.glob(os.path.join(student_dir, "*.jpg"))
    png_files = glob.glob(os.path.join(student_dir, "*.png"))
    return len(jpg_files) + len(png_files)
