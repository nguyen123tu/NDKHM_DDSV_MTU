"""
Service: Quản lý Lớp Học.
Tất cả truy vấn DB liên quan tới bảng lop_hoc đều nằm ở đây.
"""

from db.connection import execute_query, execute_one, execute_update


def get_all(active_only=True):
    """
    Lấy danh sách tất cả lớp học.
    
    Args:
        active_only: True → chỉ lấy lớp đang hoạt động
        
    Returns:
        list[dict]: Danh sách lớp học
    """
    if active_only:
        sql = """
            SELECT lh.*, 
                   (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = lh.id AND sv.trang_thai = 1) as si_so
            FROM lop_hoc lh 
            WHERE lh.trang_thai = 1 
            ORDER BY lh.id DESC
        """
    else:
        sql = """
            SELECT lh.*, 
                   (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = lh.id AND sv.trang_thai = 1) as si_so
            FROM lop_hoc lh 
            ORDER BY lh.id DESC
        """
    return execute_query(sql)


def get_by_id(class_id):
    """Lấy thông tin lớp học theo ID."""
    sql = """
        SELECT lh.*, 
               (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = lh.id AND sv.trang_thai = 1) as si_so
        FROM lop_hoc lh 
        WHERE lh.id = %s
    """
    return execute_one(sql, (class_id,))


def get_by_ma_lop(ma_lop):
    """Lấy thông tin lớp học theo mã lớp."""
    sql = """
        SELECT lh.*, 
               (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = lh.id AND sv.trang_thai = 1) as si_so
        FROM lop_hoc lh 
        WHERE lh.ma_lop = %s
    """
    return execute_one(sql, (ma_lop,))


def create(data):
    """
    Thêm lớp học mới.
    
    Args:
        data: dict với keys: ma_lop, ten_lop, khoa, hoc_ky, nam_hoc, giao_vien, mo_ta
        
    Returns:
        int: ID lớp mới, hoặc -1 nếu lỗi
    """
    sql = """
        INSERT INTO lop_hoc (ma_lop, ten_lop, khoa, hoc_ky, nam_hoc, giao_vien, mo_ta)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get("ma_lop"),
        data.get("ten_lop"),
        data.get("khoa"),
        data.get("hoc_ky"),
        data.get("nam_hoc"),
        data.get("giao_vien"),
        data.get("mo_ta")
    )
    return execute_update(sql, params)


def update(class_id, data):
    """
    Cập nhật thông tin lớp học.
    
    Returns:
        bool: True nếu thành công
    """
    allowed_fields = ["ma_lop", "ten_lop", "khoa", "hoc_ky", "nam_hoc", "giao_vien", "mo_ta", "trang_thai"]
    set_parts = []
    params = []

    for field in allowed_fields:
        if field in data:
            set_parts.append(f"{field} = %s")
            params.append(data[field])

    if not set_parts:
        return False

    params.append(class_id)
    sql = f"UPDATE lop_hoc SET {', '.join(set_parts)} WHERE id = %s"
    result = execute_update(sql, tuple(params))
    return result >= 0


def delete(class_id):
    """Xóa cứng lớp học khỏi Database."""
    sql = "DELETE FROM lop_hoc WHERE id = %s"
    result = execute_update(sql, (class_id,))
    return result >= 0


def get_students_in_class(lop_id):
    """Lấy danh sách sinh viên trong lớp."""
    sql = """
        SELECT sv.id, sv.mssv, sv.ho_ten, sv.avatar, sv.da_train, sv.email, sv.sdt
        FROM sinh_vien sv 
        WHERE sv.lop_id = %s AND sv.trang_thai = 1
        ORDER BY sv.ho_ten
    """
    return execute_query(sql, (lop_id,))


def get_attendance_summary(lop_id, date=None):
    """
    Thống kê điểm danh của lớp trong 1 ngày.
    
    Args:
        lop_id: ID lớp học
        date: Ngày cần thống kê (mặc định: hôm nay)
        
    Returns:
        dict: {"co_mat": int, "vang": int, "si_so": int, "ty_le": float}
    """
    # Đếm sĩ số lớp
    si_so_result = execute_one(
        "SELECT COUNT(*) as total FROM sinh_vien WHERE lop_id = %s AND trang_thai = 1",
        (lop_id,)
    )
    si_so = si_so_result["total"] if si_so_result else 0

    # Đếm có mặt
    if date:
        date_filter = "DATE(dd.thoi_gian) = %s"
        params = (lop_id, date)
    else:
        date_filter = "DATE(dd.thoi_gian) = CURDATE()"
        params = (lop_id,)

    co_mat_sql = f"""
        SELECT COUNT(DISTINCT dd.sinh_vien_id) as co_mat
        FROM diem_danh dd
        WHERE dd.lop_id = %s AND {date_filter} AND dd.trang_thai = 'Co mat'
    """
    co_mat_result = execute_one(co_mat_sql, params)
    co_mat = co_mat_result["co_mat"] if co_mat_result else 0

    vang = si_so - co_mat
    ty_le = (co_mat / si_so * 100) if si_so > 0 else 0

    return {
        "co_mat": co_mat,
        "vang": vang,
        "si_so": si_so,
        "ty_le": round(ty_le, 1)
    }
