"""
Service: Quản lý Điểm Danh.
Tất cả thao tác ghi nhận điểm danh ĐỀU phải đi qua record_attendance().
Không để route/thread tự ghi SQL trực tiếp.
"""

import time
from datetime import datetime, date
from db.connection import execute_query, execute_one, execute_update
from config import Config
from services.attendance_policy import AttendanceStatus, compute_status

# Bộ nhớ tạm chống ghi duplicate trong RAM (bổ sung cho DB check)
_last_log_times = {}  # {cache_key: timestamp}


def record_attendance(
    session_id,
    student_id,
    method,
    confidence=None,
    evidence_path=None,
    latitude=None,
    longitude=None,
    client_event_id=None,
    camera_id=0,
    face_image=None,
):
    """
    Ghi nhận điểm danh (1 chiều) — Hàm lõi duy nhất.

    Service tự:
    1. Kiểm tra phiên tồn tại và còn mở.
    2. Lấy lop_id từ phiên.
    3. Kiểm tra sinh viên thuộc lớp.
    4. Kiểm tra thời gian cho phép.
    5. Tính trạng thái (PRESENT / LATE).
    6. Chống trùng theo phiên.
    7. Ghi evidence.
    8. Trả kết quả thống nhất.

    Args:
        session_id: ID phiên điểm danh (bắt buộc)
        student_id: ID sinh viên (bắt buộc)
        method: Phương thức ('FACE_CAMERA', 'MOBILE_GPS', 'LEAVE_REQUEST', 'SYSTEM_AUTO')
        confidence: Độ chính xác nhận diện (do server tính)
        evidence_path: Đường dẫn ảnh bằng chứng
        latitude, longitude: Tọa độ GPS (mobile)
        client_event_id: UUID từ client cho offline dedup
        camera_id: ID camera (web)
        face_image: numpy array ảnh khuôn mặt (web camera)

    Returns:
        dict: {
            'success': bool,
            'action': 'checkin' | 'observed' | 'rejected',
            'status': str,
            'display_status': str,
            'late_minutes': int,
            'error_code': str (nếu lỗi),
            'message': str (nếu lỗi),
        }
    """
    now_dt = datetime.now()

    # ── 1. Kiểm tra phiên ──
    if not session_id:
        return _error("MISSING_SESSION", "Thiếu session_id")

    session_row = execute_one(
        "SELECT * FROM phien_diem_danh WHERE id = %s", (session_id,)
    )
    if not session_row:
        return _error("SESSION_NOT_FOUND", "Phiên điểm danh không tồn tại")

    if session_row.get("trang_thai") == 0:
        return _error("SESSION_CLOSED", "Phiên điểm danh đã đóng")

    if session_row.get("is_cancelled"):
        return _error("SESSION_CANCELLED", "Phiên điểm danh đã bị hủy")

    # Kiểm tra hết hạn
    expire_dt = session_row.get("het_han") or session_row.get("dong_checkin")
    if expire_dt and hasattr(expire_dt, "year") and now_dt > expire_dt:
        execute_update(
            "UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = GETDATE() WHERE id = %s",
            (session_id,),
        )
        return _error("SESSION_EXPIRED", "Phiên điểm danh đã hết hạn")

    lop_id = session_row["lop_id"]

    # ── 2. Kiểm tra sinh viên ──
    if not student_id:
        return _error("MISSING_STUDENT", "Thiếu student_id")

    sv = execute_one(
        "SELECT id, mssv, lop_id, ho_ten, is_locked FROM sinh_vien WHERE id = %s",
        (student_id,),
    )
    if not sv:
        return _error("STUDENT_NOT_FOUND", "Không tìm thấy sinh viên")

    if sv.get("is_locked") == 1:
        return _error("STUDENT_LOCKED", "Tài khoản sinh viên đã bị khóa")

    # ── 3. Kiểm tra sinh viên thuộc lớp ──
    if str(sv.get("lop_id")) != str(lop_id):
        return _error("WRONG_CLASS", f"Sinh viên {sv.get('mssv')} không thuộc lớp này")

    # ── 3b. GPS enforcement ──
    if session_row.get("require_gps"):
        from services.attendance_policy import validate_gps

        sess_lat = session_row.get("vi_do")
        sess_lng = session_row.get("kinh_do")
        sess_radius = session_row.get("radius") or 100

        if latitude is None or longitude is None:
            # GPS thiếu → PENDING_REVIEW (cho admin duyệt sau)
            return _error(
                "GPS_MISSING", "Phiên yêu cầu GPS nhưng thiếu tọa độ. Hãy bật GPS."
            )

        gps_valid, distance = validate_gps(
            latitude, longitude, sess_lat, sess_lng, sess_radius
        )
        if not gps_valid:
            return _error(
                "GPS_OUT_OF_RANGE",
                f"Bạn đang cách lớp {int(distance)}m (cho phép {int(sess_radius)}m)",
            )

    # ── 4. Cooldown ngắn 30s chống spam trong bộ nhớ ──
    SPAM_COOLDOWN = 30
    cache_key = f"{session_id}_{student_id}"
    last_time = _last_log_times.get(cache_key, 0)
    current_time = time.time()

    if current_time - last_time < SPAM_COOLDOWN:
        # Kiểm tra xem đã có bản ghi chưa
        existing = execute_one(
            "SELECT id, status, late_minutes FROM diem_danh WHERE phien_id = %s AND sinh_vien_id = %s",
            (session_id, student_id),
        )
        if existing:
            return {
                "success": True,
                "action": "observed",
                "status": existing.get("status", AttendanceStatus.PRESENT),
                "display_status": AttendanceStatus.display(
                    existing.get("status", AttendanceStatus.PRESENT)
                ),
                "late_minutes": existing.get("late_minutes", 0),
            }

    # ── 5. Chống trùng theo phiên (DB check) ──
    existing = execute_one(
        "SELECT id, status, late_minutes FROM diem_danh WHERE phien_id = %s AND sinh_vien_id = %s",
        (session_id, student_id),
    )
    if existing:
        _last_log_times[cache_key] = current_time
        return {
            "success": True,
            "action": "observed",
            "status": existing.get("status", AttendanceStatus.PRESENT),
            "display_status": AttendanceStatus.display(
                existing.get("status", AttendanceStatus.PRESENT)
            ),
            "late_minutes": existing.get("late_minutes", 0),
        }

    # Chống trùng offline bằng client_event_id
    if client_event_id:
        dup = execute_one(
            "SELECT id FROM diem_danh WHERE client_event_id = %s", (client_event_id,)
        )
        if dup:
            return _error("DUPLICATE_EVENT", "Bản ghi offline đã được đồng bộ trước đó")

    # ── 6. Lưu ảnh evidence nếu có ──
    image_path = evidence_path
    if face_image is not None and image_path is None:
        import cv2
        import os

        img_dir = "static/attendance_images"
        os.makedirs(img_dir, exist_ok=True)
        img_filename = (
            f"{sv.get('mssv', student_id)}_{now_dt.strftime('%Y%m%d_%H%M%S')}.jpg"
        )
        img_filepath = os.path.join(img_dir, img_filename)
        cv2.imwrite(img_filepath, face_image)
        image_path = f"attendance_images/{img_filename}"

    # ── 7 & 9. Ghi event quan sát và bản ghi điểm danh (Atomic) ──

    # Tính trạng thái
    scheduled_start = session_row.get("gio_hoc_du_kien") or session_row.get("bat_dau")
    status, late_minutes = compute_status(now_dt, scheduled_start)
    display_status = AttendanceStatus.display(status)

    ghi_chu = None
    if image_path:
        ghi_chu = f"EVIDENCE:{image_path}"
    if latitude is not None and longitude is not None:
        gps_note = f"GPS:{latitude},{longitude}"
        ghi_chu = f"{ghi_chu} | {gps_note}" if ghi_chu else gps_note

    try:
        from db.connection import transaction

        with transaction() as conn:
            cursor = conn.cursor()

            if confidence and confidence > 0:
                cursor.execute(
                    """
                    INSERT INTO attendance_events (phien_id, sinh_vien_id, event_type, observed_at, camera_id, confidence, evidence_path)
                    VALUES (%s, %s, 'FACE_OBSERVED', GETDATE(), %s, %s, %s)
                    """,
                    (session_id, student_id, camera_id, confidence, image_path),
                )

            sql = """
                INSERT INTO diem_danh (
                    phien_id, sinh_vien_id, lop_id, trang_thai, status, late_minutes,
                    method, do_chinh_xac, camera_id, ghi_chu, gio_vao_lop,
                    anh_checkin, client_event_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    session_id,
                    student_id,
                    lop_id,
                    display_status,
                    status,
                    late_minutes,
                    method,
                    confidence or 0,
                    camera_id,
                    ghi_chu,
                    now_dt.strftime("%H:%M:%S"),
                    image_path,
                    client_event_id,
                ),
            )

        _last_log_times[cache_key] = current_time

        # Gửi Push Notification (FCM)
        _send_checkin_notification(
            sv.get("mssv", ""),
            now_dt,
            camera_id,
            image_path,
            display_status,
            late_minutes,
        )

        return {
            "success": True,
            "action": "checkin",
            "status": status,
            "display_status": display_status,
            "late_minutes": late_minutes,
        }
    except Exception as e:
        error_str = str(e)
        if "uq_phien_sinh_vien" in error_str or "UNIQUE KEY" in error_str:
            _last_log_times[cache_key] = current_time
            return {
                "success": True,
                "action": "observed",
                "status": status,
                "display_status": display_status,
                "late_minutes": late_minutes,
            }
        print(f"[ATTENDANCE ERROR] {e}")
        return _error("INSERT_FAILED", "Không thể ghi nhận điểm danh do lỗi hệ thống")


def _send_checkin_notification(
    mssv, now_dt, camera_id, image_path, display_status, late_minutes
):
    """Gửi FCM push notification sau khi ghi nhận điểm danh."""
    try:
        from services.fcm_service import notify_student_attendance
        from flask import request

        time_str = now_dt.strftime("%H:%M:%S %d/%m/%Y")
        image_url = None
        try:
            if image_path:
                base_url = request.host_url.rstrip("/")
                image_url = f"{base_url}/{image_path}"
        except Exception:
            pass

        notify_student_attendance(
            mssv=mssv,
            time_str=time_str,
            camera_name=f"Camera {camera_id}",
            image_url=image_url,
            trang_thai=display_status,
            di_tre_phut=late_minutes,
        )
    except Exception:
        pass  # Notification thất bại không ảnh hưởng điểm danh


def _error(code, message):
    """Trả về dict lỗi chuẩn."""
    return {
        "success": False,
        "action": "rejected",
        "error_code": code,
        "message": message,
    }


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

    for item in items:
        # Chuẩn hóa hiển thị trạng thái
        status = item.get("status")
        if status:
            item["display_status"] = AttendanceStatus.display(status)
        else:
            item["display_status"] = item.get("trang_thai", "Không rõ")

        # Xử lý gio_vao_lop
        gio_vao_lop_td = item.get("gio_vao_lop")
        if gio_vao_lop_td is not None:
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
                parts = str(gio_vao_lop_td).split(":")
                hours, minutes = int(parts[0]), int(parts[1])
                seconds = int(parts[2].split(".")[0]) if len(parts) > 2 else 0
            item["gio_vao_lop"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            item["gio_vao_lop"] = "07:00:00"

        # Dùng late_minutes từ DB thay vì tự tính lại
        item["di_tre_phut"] = int(item.get("late_minutes") or 0)

    return {"items": items, "total": total, "pages": pages, "current": page}


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

    # Số SV có mặt hôm nay — dùng status enum
    if lop_id:
        sql = """SELECT COUNT(DISTINCT sinh_vien_id) as count
                 FROM diem_danh
                 WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE)
                 AND status IN ('PRESENT', 'LATE', 'EXCUSED_ABSENCE')
                 AND lop_id = %s"""
        result = execute_one(sql, (lop_id,))
    else:
        sql = """SELECT COUNT(DISTINCT sinh_vien_id) as count
                 FROM diem_danh
                 WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE)
                 AND status IN ('PRESENT', 'LATE', 'EXCUSED_ABSENCE')"""
        result = execute_one(sql)
    stats["co_mat"] = int(result["count"] or 0) if result else 0

    # Số cảnh báo hôm nay
    result = execute_one(
        "SELECT COUNT(*) as count FROM canh_bao WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE)"
    )
    stats["canh_bao"] = int(result["count"] or 0) if result else 0

    # Tổng lượt quét hôm nay
    result = execute_one(
        "SELECT COUNT(*) as count FROM diem_danh WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE)"
    )
    stats["tong_luot"] = int(result["count"] or 0) if result else 0

    # Số lớp tham gia hôm nay
    result = execute_one(
        "SELECT COUNT(DISTINCT lop_id) as count FROM diem_danh WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE) AND lop_id IS NOT NULL"
    )
    stats["lop_dang_diem_danh"] = int(result["count"] or 0) if result else 0

    return stats


def get_student_history(mssv, limit=30):
    """Lấy lịch sử điểm danh cá nhân của 1 sinh viên."""
    sql = """
        SELECT dd.thoi_gian, dd.trang_thai, dd.status, dd.late_minutes,
               dd.do_chinh_xac, dd.gio_ra, dd.anh_checkin, dd.anh_checkout,
               lh.ten_lop, lh.ma_lop
        FROM diem_danh dd
        LEFT JOIN sinh_vien sv ON dd.sinh_vien_id = sv.id
        LEFT JOIN lop_hoc lh ON dd.lop_id = lh.id
        WHERE sv.mssv = %s
        ORDER BY thoi_gian DESC
        OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
    """
    results = execute_query(sql, (mssv, limit))
    for r in results:
        status = r.get("status")
        if status:
            r["display_status"] = AttendanceStatus.display(status)
    return results


def get_weekly_chart_data(lop_id=None):
    """
    Dữ liệu biểu đồ 7 ngày gần nhất (cho Dashboard).
    Dùng status enum thay vì trang_thai tiếng Việt.

    Returns:
        list[dict]: [{"ngay": "2026-04-14", "co_mat": 25, "canh_bao": 2}, ...]
    """
    if lop_id:
        sql = """
            SELECT CAST(thoi_gian AS DATE) as ngay,
                   COUNT(DISTINCT CASE WHEN status IN ('PRESENT', 'LATE') THEN sinh_vien_id END) as co_mat,
                   COUNT(CASE WHEN status = 'INVALID' THEN 1 END) as canh_bao
            FROM diem_danh
            WHERE thoi_gian >= DATEADD(day, -6, CAST(GETDATE() AS DATE)) AND lop_id = %s
            GROUP BY CAST(thoi_gian AS DATE)
            ORDER BY ngay
        """
        return execute_query(sql, (lop_id,))
    else:
        sql = """
            SELECT CAST(thoi_gian AS DATE) as ngay,
                   COUNT(DISTINCT CASE WHEN status IN ('PRESENT', 'LATE') THEN sinh_vien_id END) as co_mat,
                   COUNT(CASE WHEN status = 'INVALID' THEN 1 END) as canh_bao
            FROM diem_danh
            WHERE thoi_gian >= DATEADD(day, -6, CAST(GETDATE() AS DATE))
            GROUP BY CAST(thoi_gian AS DATE)
            ORDER BY ngay
        """
        return execute_query(sql)


def get_top_absent_students(limit=5):
    """
    Lấy top sinh viên có tỷ lệ vắng mặt cao nhất trong 30 ngày gần nhất.
    Dùng phiên đã đóng làm chuẩn thay vì đếm ngày có điểm danh.
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
        JOIN (
            SELECT lop_id, COUNT(*) as tong_buoi
            FROM phien_diem_danh
            WHERE trang_thai = 0
              AND ISNULL(is_cancelled, 0) = 0
              AND bat_dau >= DATEADD(day, -30, CAST(GETDATE() AS DATE))
            GROUP BY lop_id
        ) total_sessions ON total_sessions.lop_id = sv.lop_id
        LEFT JOIN (
            SELECT sinh_vien_id, d.lop_id, COUNT(*) as so_buoi_di
            FROM diem_danh d
            JOIN phien_diem_danh p ON d.phien_id = p.id
            WHERE p.trang_thai = 0
              AND ISNULL(p.is_cancelled, 0) = 0
              AND p.bat_dau >= DATEADD(day, -30, CAST(GETDATE() AS DATE))
              AND d.status IN ('PRESENT', 'LATE')
            GROUP BY sinh_vien_id, d.lop_id
        ) attended ON attended.sinh_vien_id = sv.id AND attended.lop_id = sv.lop_id
        WHERE sv.trang_thai = 1
          AND total_sessions.tong_buoi > 0
        ORDER BY so_buoi_vang DESC, sv.mssv ASC
        OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
    """
    results = execute_query(sql, (limit,))

    for r in results:
        tong = int(r.get("tong_buoi") or 1)
        vang = int(r.get("so_buoi_vang") or 0)
        r["ty_le_vang"] = round((vang / tong) * 100, 1) if tong > 0 else 0

    return results


# ─── Backward compatibility: giữ hàm log() gọi vào record_attendance() ──────


def log(
    mssv,
    lop_id=None,
    do_chinh_xac=0.0,
    camera_id=0,
    trang_thai=None,
    ghi_chu=None,
    session_start_time=None,
    class_start_time="07:00:00",
    face_image=None,
    phien_id=None,
    method="FACE_CAMERA",
):
    """
    [DEPRECATED] Wrapper backward-compatible. Gọi record_attendance() bên trong.
    Các caller cũ vẫn dùng được, nhưng caller mới nên gọi record_attendance() trực tiếp.
    """
    # Tìm sinh_vien_id từ mssv
    sv = execute_one("SELECT id, lop_id FROM sinh_vien WHERE mssv = %s", (mssv,))
    if not sv:
        return False

    student_id = sv["id"]
    if not lop_id:
        lop_id = sv["lop_id"]

    # Nếu chưa truyền phien_id, thử tìm phiên đang mở
    if not phien_id and lop_id:
        from services.attendance_session_service import AttendanceSessionService

        active_sess = AttendanceSessionService.get_active_session(lop_id=lop_id)
        if active_sess:
            phien_id = active_sess["id"]

    if not phien_id:
        return False  # Không có phiên thì không ghi

    result = record_attendance(
        session_id=phien_id,
        student_id=student_id,
        method=method,
        confidence=do_chinh_xac,
        camera_id=camera_id,
        face_image=face_image,
    )

    if not result or not result.get("success"):
        return False

    # Chuyển đổi format cho caller cũ
    return {
        "action": result.get("action", "checkin"),
        "success": True,
        "trang_thai": result.get("display_status", "Có mặt"),
        "status": result.get("status", AttendanceStatus.PRESENT),
        "late_minutes": result.get("late_minutes", 0),
    }
