"""
Service: Quản lý Điểm Danh.
Ghi nhận log điểm danh, tránh duplicate, thống kê.
"""

import time
from db.connection import execute_query, execute_one, execute_update
from config import Config


# Bộ nhớ tạm chống ghi duplicate trong RAM (bổ sung cho DB check)
_last_log_times = {}  # {mssv: timestamp}


def log(mssv, lop_id=None, do_chinh_xac=0.0, camera_id=0, trang_thai='Co mat'):
    """
    Ghi nhận điểm danh: Giờ Vào / Giờ Ra.
    
    Logic:
    - Lần quét đầu tiên trong ngày → INSERT mới (giờ vào)
    - Lần quét sau (cách >= 30 phút) → UPDATE gio_ra (giờ ra)
    - Lần quét trong cooldown 60s → Bỏ qua (tránh spam)
    
    Args:
        mssv, lop_id, do_chinh_xac, camera_id, trang_thai
        
    Returns:
        dict: {'action': 'checkin'/'checkout'/'skip', 'success': bool}
              hoặc False nếu bỏ qua hoàn toàn
    """
    current_time = time.time()
    
    # Cooldown ngắn 60s chống spam (tránh ghi liên tục khi đứng trước camera)
    SPAM_COOLDOWN = 60
    cache_key = f"{mssv}_{lop_id}"
    last_time = _last_log_times.get(cache_key, 0)
    if current_time - last_time < SPAM_COOLDOWN:
        return False  # Quá gần → bỏ qua

    # Tìm sinh_vien_id
    sv = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,))
    sinh_vien_id = sv["id"] if sv else None
    if not sinh_vien_id:
        return False

    # Kiểm tra: hôm nay đã có bản ghi điểm danh chưa?
    existing = execute_one("""
        SELECT id, thoi_gian, gio_ra 
        FROM diem_danh 
        WHERE sinh_vien_id = %s AND lop_id = %s 
          AND DATE(thoi_gian) = CURDATE()
        ORDER BY thoi_gian DESC
        LIMIT 1
    """, (sinh_vien_id, lop_id))

    if existing is None:
        # === CHƯA CÓ → GHI GIỜ VÀO (CHECK-IN) ===
        sql = """
            INSERT INTO diem_danh (sinh_vien_id, lop_id, trang_thai, do_chinh_xac, camera_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        result = execute_update(sql, (sinh_vien_id, lop_id, trang_thai, do_chinh_xac, camera_id))
        if result > 0:
            _last_log_times[cache_key] = current_time
            return {'action': 'checkin', 'success': True}
        return False
    
    else:
        # === ĐÃ CÓ BẢN GHI HÔM NAY ===
        if existing.get('gio_ra') is not None:
            # Đã có cả giờ vào + giờ ra → hoàn tất, không ghi nữa
            _last_log_times[cache_key] = current_time
            return False
        
        # Chưa có giờ ra → cập nhật giờ ra (nếu cách giờ vào >= 30 phút)
        from datetime import datetime, timedelta
        gio_vao = existing['thoi_gian']
        now = datetime.now()
        
        # Phải cách ít nhất 30 phút so với giờ vào mới coi là "giờ ra"
        MIN_CHECKOUT_GAP = timedelta(minutes=30)
        if now - gio_vao >= MIN_CHECKOUT_GAP:
            sql = "UPDATE diem_danh SET gio_ra = NOW() WHERE id = %s"
            result = execute_update(sql, (existing['id'],))
            if result > 0:
                _last_log_times[cache_key] = current_time
                return {'action': 'checkout', 'success': True}
        
        # Chưa đủ 30 phút → bỏ qua
        _last_log_times[cache_key] = current_time
        return False


def log_unknown(camera_id=0, anh_chup=None, ghi_chu=None):
    """
    Ghi nhận cảnh báo người lạ vào bảng canh_bao.
    
    Args:
        camera_id: ID camera phát hiện
        anh_chup: Đường dẫn ảnh chụp
        ghi_chu: Ghi chú thêm
        
    Returns:
        bool: True nếu thành công
    """
    sql = """
        INSERT INTO canh_bao (camera_id, anh_chup, ghi_chu)
        VALUES (%s, %s, %s)
    """
    result = execute_update(sql, (camera_id, anh_chup, ghi_chu))
    return result > 0


def get_history(lop_id=None, date=None, mssv=None, page=1, per_page=50):
    """
    Lấy lịch sử điểm danh có phân trang và filter.
    
    Returns:
        dict: {"items": list, "total": int, "pages": int, "current": int}
    """
    conditions = ["1=1"]
    params = []

    if lop_id:
        conditions.append("dd.lop_id = %s")
        params.append(lop_id)

    if date:
        conditions.append("DATE(dd.thoi_gian) = %s")
        params.append(date)

    if mssv:
        conditions.append("sv.mssv = %s")
        params.append(mssv)

    where_clause = " AND ".join(conditions)

    # Đếm tổng
    count_sql = f"""
        SELECT COUNT(*) as total 
        FROM diem_danh dd
        LEFT JOIN sinh_vien sv ON dd.sinh_vien_id = sv.id
        WHERE {where_clause}
    """
    count_result = execute_one(count_sql, tuple(params) if params else None)
    total = count_result["total"] if count_result else 0

    pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page

    # Query dữ liệu
    data_sql = f"""
        SELECT dd.*, sv.mssv, sv.ho_ten, sv.avatar, lh.ten_lop, lh.ma_lop
        FROM diem_danh dd
        LEFT JOIN sinh_vien sv ON dd.sinh_vien_id = sv.id
        LEFT JOIN lop_hoc lh ON dd.lop_id = lh.id
        WHERE {where_clause}
        ORDER BY dd.thoi_gian DESC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    items = execute_query(data_sql, tuple(params))

    return {
        "items": items,
        "total": total,
        "pages": pages,
        "current": page
    }


def get_today_summary(lop_id=None):
    """
    Thống kê điểm danh hôm nay.
    
    Returns:
        dict: {
            "co_mat": int,       — Số sinh viên có mặt
            "canh_bao": int,     — Số cảnh báo kẻ lạ
            "tong_luot": int,    — Tổng lượt quét
            "lop_dang_diem_danh": int — Số lớp đang điểm danh
        }
    """
    stats = {}

    # Số SV có mặt hôm nay (distinct)
    if lop_id:
        sql = """SELECT COUNT(DISTINCT sinh_vien_id) as count 
                 FROM diem_danh WHERE DATE(thoi_gian) = CURDATE() 
                 AND trang_thai = 'Co mat' AND lop_id = %s"""
        result = execute_one(sql, (lop_id,))
    else:
        sql = """SELECT COUNT(DISTINCT sinh_vien_id) as count 
                 FROM diem_danh WHERE DATE(thoi_gian) = CURDATE() 
                 AND trang_thai = 'Co mat'"""
        result = execute_one(sql)
    stats["co_mat"] = result["count"] if result else 0

    # Số cảnh báo hôm nay
    result = execute_one(
        "SELECT COUNT(*) as count FROM canh_bao WHERE DATE(thoi_gian) = CURDATE()"
    )
    stats["canh_bao"] = result["count"] if result else 0

    # Tổng lượt quét hôm nay
    result = execute_one(
        "SELECT COUNT(*) as count FROM diem_danh WHERE DATE(thoi_gian) = CURDATE()"
    )
    stats["tong_luot"] = result["count"] if result else 0

    # Số lớp tham gia hôm nay
    result = execute_one(
        "SELECT COUNT(DISTINCT lop_id) as count FROM diem_danh WHERE DATE(thoi_gian) = CURDATE() AND lop_id IS NOT NULL"
    )
    stats["lop_dang_diem_danh"] = result["count"] if result else 0

    return stats


def get_student_history(mssv, limit=30):
    """Lấy lịch sử điểm danh cá nhân của 1 sinh viên."""
    sql = """
        SELECT dd.thoi_gian, dd.trang_thai, dd.do_chinh_xac, lh.ten_lop, lh.ma_lop
        FROM diem_danh dd
        LEFT JOIN sinh_vien sv ON dd.sinh_vien_id = sv.id
        LEFT JOIN lop_hoc lh ON dd.lop_id = lh.id
        WHERE sv.mssv = %s
        ORDER BY dd.thoi_gian DESC
        LIMIT %s
    """
    return execute_query(sql, (mssv, limit))


def get_weekly_chart_data(lop_id=None):
    """
    Dữ liệu biểu đồ 7 ngày gần nhất (cho Dashboard).
    
    Returns:
        list[dict]: [{"ngay": "2026-04-14", "co_mat": 25, "canh_bao": 2}, ...]
    """
    if lop_id:
        sql = """
            SELECT DATE(thoi_gian) as ngay,
                   COUNT(DISTINCT CASE WHEN trang_thai = 'Co mat' THEN sinh_vien_id END) as co_mat,
                   COUNT(CASE WHEN trang_thai = 'Canh bao' THEN 1 END) as canh_bao
            FROM diem_danh
            WHERE thoi_gian >= DATE_SUB(CURDATE(), INTERVAL 6 DAY) AND lop_id = %s
            GROUP BY DATE(thoi_gian)
            ORDER BY ngay
        """
        return execute_query(sql, (lop_id,))
    else:
        sql = """
            SELECT DATE(thoi_gian) as ngay,
                   COUNT(DISTINCT CASE WHEN trang_thai = 'Co mat' THEN sinh_vien_id END) as co_mat,
                   COUNT(CASE WHEN trang_thai = 'Canh bao' THEN 1 END) as canh_bao
            FROM diem_danh
            WHERE thoi_gian >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            GROUP BY DATE(thoi_gian)
            ORDER BY ngay
        """
        return execute_query(sql)


def get_top_absent_students(limit=5):
    """
    Lấy top sinh viên có tỷ lệ vắng mặt cao nhất trong 30 ngày gần nhất.
    
    Logic: Đếm số ngày lớp có điểm danh (distinct DATE) trong 30 ngày,
    sau đó so sánh với số ngày sinh viên thực sự có mặt.
    
    Returns:
        list[dict]: [{mssv, ho_ten, ten_lop, so_buoi_vang, tong_buoi, ty_le_vang}, ...]
    """
    sql = """
        SELECT 
            sv.mssv,
            sv.ho_ten,
            lh.ten_lop,
            total_sessions.tong_buoi,
            COALESCE(attended.so_buoi_di, 0) as so_buoi_di,
            (total_sessions.tong_buoi - COALESCE(attended.so_buoi_di, 0)) as so_buoi_vang
        FROM sinh_vien sv
        JOIN lop_hoc lh ON sv.lop_id = lh.id
        -- Tính tổng số buổi điểm danh của lớp trong 30 ngày
        JOIN (
            SELECT lop_id, COUNT(DISTINCT DATE(thoi_gian)) as tong_buoi
            FROM diem_danh
            WHERE thoi_gian >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY lop_id
        ) total_sessions ON total_sessions.lop_id = sv.lop_id
        -- Tính số buổi sinh viên có mặt
        LEFT JOIN (
            SELECT sinh_vien_id, lop_id, COUNT(DISTINCT DATE(thoi_gian)) as so_buoi_di
            FROM diem_danh
            WHERE thoi_gian >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) AND trang_thai = 'Co mat'
            GROUP BY sinh_vien_id, lop_id
        ) attended ON attended.sinh_vien_id = sv.id AND attended.lop_id = sv.lop_id
        WHERE sv.trang_thai = 1
          AND total_sessions.tong_buoi > 0
        ORDER BY so_buoi_vang DESC, sv.mssv ASC
        LIMIT %s
    """
    results = execute_query(sql, (limit,))
    
    # Tính tỷ lệ vắng
    for r in results:
        tong = r.get("tong_buoi", 1)
        vang = r.get("so_buoi_vang", 0)
        r["ty_le_vang"] = round((vang / tong) * 100, 1) if tong > 0 else 0
    
    return results

