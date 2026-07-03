"""
Service: Quản lý Điểm Danh.
Ghi nhận log điểm danh, tránh duplicate, thống kê.
"""

import time
from db.connection import execute_query, execute_one, execute_update
from config import Config


# Bộ nhớ tạm chống ghi duplicate trong RAM (bổ sung cho DB check)
_last_log_times = {}  # {mssv: timestamp}


def log(mssv, lop_id=None, do_chinh_xac=0.0, camera_id=0, trang_thai='Co mat', ghi_chu=None, session_start_time=None, class_start_time="07:00:00"):
    """
    Ghi nhận điểm danh (1 chiều).
    
    Args:
        mssv, lop_id, do_chinh_xac, camera_id, trang_thai, ghi_chu
        session_start_time: (datetime or str) Nếu có, chỉ check duplicate trong khoảng thời gian diễn ra phiên.
        
    Returns:
        dict: {'action': 'checkin'/'skip', 'success': bool}
    """
    current_time = time.time()
    
    # Cooldown ngắn 60s chống spam (bỏ qua cooldown nếu check_in cụ thể cho một phiên mới mở)
    SPAM_COOLDOWN = 60
    cache_key = f"{mssv}_{lop_id}"
    last_time = _last_log_times.get(cache_key, 0)
    
    if current_time - last_time < SPAM_COOLDOWN and not session_start_time:
        return False

    # Tìm sinh_vien_id
    sv = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,))
    sinh_vien_id = sv["id"] if sv else None
    if not sinh_vien_id:
        return False

    # Parse class_start_time (usually "HH:MM")
    # Ensure it has seconds
    if len(class_start_time.split(':')) == 2:
        class_start_time += ":00"

    # Kiểm tra: hôm nay đã có bản ghi điểm danh chưa?
    if session_start_time:
        existing = execute_one("""
            SELECT TOP 1 * FROM diem_danh
            WHERE sinh_vien_id = %s AND lop_id = %s AND CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE)
            ORDER BY id DESC
        """, (sinh_vien_id, lop_id))
    else:
        existing = execute_one("""
            SELECT TOP 1 id, thoi_gian
            FROM diem_danh 
            WHERE sinh_vien_id = %s AND lop_id = %s 
              AND CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE)
              AND gio_vao_lop = %s
            ORDER BY thoi_gian DESC
        """, (sinh_vien_id, lop_id, class_start_time))

    if existing is None:
        from datetime import datetime, date
        
        start_time_obj = datetime.strptime(class_start_time, "%H:%M:%S").time()
        target_dt = datetime.combine(date.today(), start_time_obj)
        now_dt = datetime.now()
        
        diff = now_dt - target_dt
        di_tre_phut = int(diff.total_seconds() / 60)
        
        grace_period = getattr(Config, 'LATE_GRACE_PERIOD_MIN', 15)
        
        if di_tre_phut > grace_period and trang_thai == 'Co mat':
            trang_thai = 'Tre'
        else:
            if trang_thai == 'Co mat':
                di_tre_phut = 0 # Đi sớm hoặc đúng giờ (trong thời gian du di)

        # CHECK-IN
        sql = """
            INSERT INTO diem_danh (sinh_vien_id, lop_id, trang_thai, do_chinh_xac, camera_id, ghi_chu, gio_vao_lop)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        result = execute_update(sql, (sinh_vien_id, lop_id, trang_thai, do_chinh_xac, camera_id, ghi_chu, class_start_time))
        if result > 0:
            _last_log_times[cache_key] = current_time
            
            # Gửi Push Notification (FCM)
            from services.fcm_service import notify_student_attendance
            from datetime import datetime
            from flask import request
            
            time_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            image_url = None
            if ghi_chu and ghi_chu.startswith("EVIDENCE:"):
                evidence_rel_path = ghi_chu.split("EVIDENCE:")[1]
                # Construct full URL for the image
                base_url = request.host_url.rstrip('/')
                # evidence_rel_path is something like evidence/20260524/...
                # But wait, we added the route /evidence/<path:filename> 
                # So we need to map evidence/... to /evidence/...
                if evidence_rel_path.startswith("evidence/"):
                    image_url = f"{base_url}/{evidence_rel_path}"
                    
            notify_student_attendance(
                mssv=mssv, 
                time_str=time_str, 
                camera_name=f"Camera {camera_id}", 
                image_url=image_url, 
                trang_thai=trang_thai, 
                di_tre_phut=di_tre_phut
            )
            
            return {'action': 'checkin', 'success': True, 'trang_thai': trang_thai}
    
    return False


def mobile_checkout(mssv, lop_id=None, camera_id=0):
    """
    Checkout tường minh cho mobile:
    Hệ thống hiện tại chỉ nhận diện 1 chiều nên đã bỏ chức năng này.
    """
    return {"success": False, "message": "Hệ thống chỉ điểm danh 1 chiều."}


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
        conditions.append("CAST(dd.thoi_gian AS DATE) = %s")
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
        OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
    """
    params.extend([offset, per_page])
    items = execute_query(data_sql, tuple(params))
    
    from datetime import datetime
    for item in items:
        # Get gio_vao_lop from item, or fallback
        # gio_vao_lop is a timedelta in Python when queried from MySQL TIME column
        gio_vao_lop_td = item.get('gio_vao_lop')
        
        if gio_vao_lop_td is not None:
            # Handle both timedelta (MySQL) and datetime.time (SQL Server)
            from datetime import timedelta, time as datetime_time_cls
            if isinstance(gio_vao_lop_td, timedelta):
                total_secs = int(gio_vao_lop_td.total_seconds())
                hours = total_secs // 3600
                minutes = (total_secs % 3600) // 60
                seconds = total_secs % 60
            elif isinstance(gio_vao_lop_td, datetime_time_cls):
                hours = gio_vao_lop_td.hour
                minutes = gio_vao_lop_td.minute
                seconds = gio_vao_lop_td.second
            else:
                # Fallback: try to parse as string
                parts = str(gio_vao_lop_td).split(':')
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2].split('.')[0]) if len(parts) > 2 else 0
            gio_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            item['gio_vao_lop'] = gio_str
            start_time_obj = datetime.strptime(gio_str, "%H:%M:%S").time()
        else:
            item['gio_vao_lop'] = "07:00:00"
            from datetime import time as datetime_time
            start_time_obj = datetime_time(7, 0, 0)
            
        item['di_tre_phut'] = 0
        if item.get('thoi_gian'):
            t = item['thoi_gian']
            target_dt = datetime.combine(t.date(), start_time_obj)
            if t > target_dt:
                diff = t - target_dt
                item['di_tre_phut'] = int(diff.total_seconds() / 60)

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
                 FROM diem_danh WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE) 
                 AND trang_thai = 'Co mat' AND lop_id = %s"""
        result = execute_one(sql, (lop_id,))
    else:
        sql = """SELECT COUNT(DISTINCT sinh_vien_id) as count 
                 FROM diem_danh WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE) 
                 AND trang_thai = 'Co mat'"""
        result = execute_one(sql)
    stats["co_mat"] = result["count"] if result else 0

    # Số cảnh báo hôm nay
    result = execute_one(
        "SELECT COUNT(*) as count FROM canh_bao WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE)"
    )
    stats["canh_bao"] = result["count"] if result else 0

    # Tổng lượt quét hôm nay
    result = execute_one(
        "SELECT COUNT(*) as count FROM diem_danh WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE)"
    )
    stats["tong_luot"] = result["count"] if result else 0

    # Số lớp tham gia hôm nay
    result = execute_one(
        "SELECT COUNT(DISTINCT lop_id) as count FROM diem_danh WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE) AND lop_id IS NOT NULL"
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
        ORDER BY thoi_gian DESC
        OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
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
            SELECT CAST(thoi_gian AS DATE) as ngay,
                   COUNT(DISTINCT CASE WHEN trang_thai = 'Co mat' THEN sinh_vien_id END) as co_mat,
                   COUNT(CASE WHEN trang_thai = 'Canh bao' THEN 1 END) as canh_bao
            FROM diem_danh
            WHERE thoi_gian >= DATEADD(day, -6, CAST(GETDATE() AS DATE)) AND lop_id = %s
            GROUP BY CAST(thoi_gian AS DATE)
            ORDER BY ngay
        """
        return execute_query(sql, (lop_id,))
    else:
        sql = """
            SELECT CAST(thoi_gian AS DATE) as ngay,
                   COUNT(DISTINCT CASE WHEN trang_thai = 'Co mat' THEN sinh_vien_id END) as co_mat,
                   COUNT(CASE WHEN trang_thai = 'Canh bao' THEN 1 END) as canh_bao
            FROM diem_danh
            WHERE thoi_gian >= DATEADD(day, -6, CAST(GETDATE() AS DATE))
            GROUP BY CAST(thoi_gian AS DATE)
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
            SELECT lop_id, COUNT(DISTINCT CAST(thoi_gian AS DATE)) as tong_buoi
            FROM diem_danh
            WHERE thoi_gian >= DATEADD(day, -30, CAST(GETDATE() AS DATE))
            GROUP BY lop_id
        ) total_sessions ON total_sessions.lop_id = sv.lop_id
        -- Tính số buổi sinh viên có mặt
        LEFT JOIN (
            SELECT sinh_vien_id, lop_id, COUNT(DISTINCT CAST(thoi_gian AS DATE)) as so_buoi_di
            FROM diem_danh
            WHERE thoi_gian >= DATEADD(day, -30, CAST(GETDATE() AS DATE)) AND trang_thai = 'Co mat'
            GROUP BY sinh_vien_id, lop_id
        ) attended ON attended.sinh_vien_id = sv.id AND attended.lop_id = sv.lop_id
        WHERE sv.trang_thai = 1
          AND total_sessions.tong_buoi > 0
        ORDER BY so_buoi_vang DESC, sv.mssv ASC
        OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
    """
    results = execute_query(sql, (limit,))
    
    # Tính tỷ lệ vắng
    for r in results:
        tong = r.get("tong_buoi", 1)
        vang = r.get("so_buoi_vang", 0)
        r["ty_le_vang"] = round((vang / tong) * 100, 1) if tong > 0 else 0
    
    return results

