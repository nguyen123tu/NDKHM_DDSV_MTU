"""
Attendance Policy Module.
Quy tắc nghiệp vụ duy nhất cho toàn bộ hệ thống điểm danh.
Tất cả logic tính trạng thái, thống kê tập trung tại đây.
Dashboard, Excel, PDF, Telegram đều phải gọi vào module này.
"""

import math
from datetime import datetime
from config import Config
from db.connection import execute_query, execute_one


# ─── Enum trạng thái chuẩn hóa (DB/API dùng mã tiếng Anh) ─────────────────

class AttendanceStatus:
    PRESENT = "PRESENT"                       # Có mặt đúng giờ
    LATE = "LATE"                             # Có mặt nhưng đi trễ
    EXCUSED_ABSENCE = "EXCUSED_ABSENCE"       # Vắng có phép
    UNEXCUSED_ABSENCE = "UNEXCUSED_ABSENCE"   # Vắng không phép
    PENDING_REVIEW = "PENDING_REVIEW"         # Chờ giảng viên duyệt
    INVALID = "INVALID"                       # Kết quả không hợp lệ
    EARLY_LEAVE = "EARLY_LEAVE"               # Rời lớp sớm

    ALL = [PRESENT, LATE, EXCUSED_ABSENCE, UNEXCUSED_ABSENCE,
           PENDING_REVIEW, INVALID, EARLY_LEAVE]

    # Mapping sang tiếng Việt cho giao diện
    DISPLAY_VI = {
        PRESENT: "Có mặt",
        LATE: "Đi trễ",
        EXCUSED_ABSENCE: "Vắng có phép",
        UNEXCUSED_ABSENCE: "Vắng không phép",
        PENDING_REVIEW: "Chờ duyệt",
        INVALID: "Không hợp lệ",
        EARLY_LEAVE: "Về sớm",
    }

    # Mapping ký hiệu cho báo cáo
    SYMBOL = {
        PRESENT: "P",
        LATE: "L",
        EXCUSED_ABSENCE: "E",
        UNEXCUSED_ABSENCE: "A",
        PENDING_REVIEW: "?",
        INVALID: "X",
        EARLY_LEAVE: "EL",
    }

    @classmethod
    def display(cls, status):
        """Trả về tên hiển thị tiếng Việt."""
        return cls.DISPLAY_VI.get(status, status or "Không rõ")

    @classmethod
    def symbol(cls, status):
        """Trả về ký hiệu ngắn cho báo cáo."""
        return cls.SYMBOL.get(status, "?")

    @classmethod
    def is_present_group(cls, status):
        """Có mặt (đúng giờ hoặc trễ)."""
        return status in (cls.PRESENT, cls.LATE)


# ─── Tính trạng thái điểm danh ───────────────────────────────────────────────

def compute_status(checkin_time, scheduled_start, grace_period=None):
    """
    Tính trạng thái điểm danh dựa trên thời gian check-in và giờ học dự kiến.

    Args:
        checkin_time: datetime — Thời gian sinh viên check-in
        scheduled_start: datetime — Giờ bắt đầu tiết học theo lịch
        grace_period: int (phút) — Thời gian cho phép trước khi tính trễ

    Returns:
        (status: str, late_minutes: int)
    """
    if grace_period is None:
        grace_period = getattr(Config, 'LATE_GRACE_PERIOD_MIN', 15)

    if not scheduled_start or not checkin_time:
        return AttendanceStatus.PRESENT, 0

    # Đảm bảo cả hai đều là datetime
    if not hasattr(scheduled_start, 'year'):
        return AttendanceStatus.PRESENT, 0

    diff_seconds = (checkin_time - scheduled_start).total_seconds()

    if diff_seconds <= 0:
        # Check-in trước hoặc đúng giờ
        return AttendanceStatus.PRESENT, 0

    late_minutes = int(diff_seconds / 60)

    if late_minutes <= grace_period:
        return AttendanceStatus.PRESENT, 0
    else:
        return AttendanceStatus.LATE, late_minutes


# ─── Kiểm tra GPS ────────────────────────────────────────────────────────────

def validate_gps(sv_lat, sv_lng, session_lat, session_lng, radius=100):
    """
    Kiểm tra vị trí GPS của sinh viên so với vị trí lớp học.

    Args:
        sv_lat, sv_lng: Tọa độ sinh viên
        session_lat, session_lng: Tọa độ phiên/lớp
        radius: Bán kính cho phép (mét)

    Returns:
        (is_valid: bool, distance: float) — distance tính bằng mét
    """
    if sv_lat is None or sv_lng is None:
        return False, -1

    if session_lat is None or session_lng is None:
        return True, 0  # Không có tọa độ phiên → bỏ qua kiểm tra

    distance = _haversine_distance(
        float(sv_lat), float(sv_lng),
        float(session_lat), float(session_lng)
    )

    return distance <= radius, distance


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách (mét) giữa 2 tọa độ GPS theo công thức Haversine."""
    R = 6371000  # Bán kính Trái Đất (mét)
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ─── Thống kê phiên — Hàm dùng chung cho Dashboard/Excel/PDF/Telegram ──────

def get_session_attendance_summary(session_id):
    """
    Thống kê tổng hợp cho một phiên điểm danh.
    Dashboard, Excel, PDF, Telegram ĐỀU PHẢI gọi hàm này.
    Không để mỗi nơi tự viết công thức khác nhau.

    Returns:
        dict: {
            "session_id": int,
            "lop_id": int,
            "ma_lop": str,
            "ten_lop": str,
            "giao_vien": str,
            "bat_dau": datetime,
            "ket_thuc": datetime,
            "gio_hoc_du_kien": datetime,
            "trang_thai_phien": int,
            "is_cancelled": bool,
            "si_so_chot": int,
            "nguoi_chot_id": int,
            "thoi_gian_chot": datetime,
            "total_students": int,
            "present": int,
            "late": int,
            "excused": int,
            "unexcused": int,
            "pending": int,
            "invalid": int,
            "early_leave": int,
            "attendance_rate": float,
            "weighted_score_rate": float,
            "records": list[dict],
        }
        None nếu phiên không tồn tại.
    """
    session_row = execute_one(
        """SELECT p.*, l.ma_lop, l.ten_lop, l.giao_vien
           FROM phien_diem_danh p
           JOIN lop_hoc l ON p.lop_id = l.id
           WHERE p.id = %s""",
        (session_id,)
    )
    if not session_row:
        return None

    lop_id = session_row['lop_id']

    # Lấy tất cả sinh viên trong lớp
    students = execute_query(
        "SELECT id, mssv, ho_ten, avatar FROM sinh_vien WHERE lop_id = %s AND trang_thai = 1 ORDER BY mssv ASC",
        (lop_id,)
    )
    total_students = len(students)

    # Lấy tất cả bản ghi điểm danh trong phiên
    dd_records = execute_query(
        """SELECT d.*, sv.mssv, sv.ho_ten, sv.avatar
           FROM diem_danh d
           JOIN sinh_vien sv ON d.sinh_vien_id = sv.id
           WHERE d.phien_id = %s
           ORDER BY sv.mssv ASC""",
        (session_id,)
    )

    # Đếm theo trạng thái
    counts = {s: 0 for s in AttendanceStatus.ALL}
    records = []

    for r in dd_records:
        st = r.get('status') or AttendanceStatus.PRESENT
        if st in counts:
            counts[st] += 1
        else:
            counts[AttendanceStatus.UNEXCUSED_ABSENCE] += 1

        records.append({
            "attendance_id": r.get("id"),
            "sinh_vien_id": r.get("sinh_vien_id"),
            "mssv": r.get("mssv", ""),
            "ho_ten": r.get("ho_ten", ""),
            "avatar": r.get("avatar", ""),
            "status": st,
            "display_status": AttendanceStatus.display(st),
            "symbol": AttendanceStatus.symbol(st),
            "late_minutes": r.get("late_minutes", 0),
            "method": r.get("method", ""),
            "thoi_gian": r.get("thoi_gian"),
            "ghi_chu": r.get("ghi_chu", ""),
            "do_chinh_xac": r.get("do_chinh_xac", 0),
        })

    si_so_chot = session_row.get('si_so_chot') or total_students
    present_count = counts[AttendanceStatus.PRESENT]
    late_count = counts[AttendanceStatus.LATE]
    excused_count = counts[AttendanceStatus.EXCUSED_ABSENCE]
    unexcused_count = counts[AttendanceStatus.UNEXCUSED_ABSENCE]

    # Tỷ lệ tham dự = (có mặt + đi trễ) / sĩ số
    attendance_rate = ((present_count + late_count) / max(1, si_so_chot)) * 100

    # Điểm chuyên cần có trọng số
    w_p = getattr(Config, 'WEIGHT_PRESENT', 1.0)
    w_l = getattr(Config, 'WEIGHT_LATE', 0.75)
    w_e = getattr(Config, 'WEIGHT_EXCUSED', 1.0)
    weighted = (present_count * w_p + late_count * w_l + excused_count * w_e)
    weighted_score_rate = (weighted / max(1, si_so_chot)) * 100

    return {
        "session_id": session_id,
        "lop_id": lop_id,
        "ma_lop": session_row.get("ma_lop", ""),
        "ten_lop": session_row.get("ten_lop", ""),
        "giao_vien": session_row.get("giao_vien", ""),
        "bat_dau": session_row.get("bat_dau"),
        "ket_thuc": session_row.get("ket_thuc"),
        "gio_hoc_du_kien": session_row.get("gio_hoc_du_kien"),
        "trang_thai_phien": session_row.get("trang_thai", 0),
        "is_cancelled": bool(session_row.get("is_cancelled", 0)),
        "si_so_chot": si_so_chot,
        "nguoi_chot_id": session_row.get("nguoi_chot_id"),
        "thoi_gian_chot": session_row.get("thoi_gian_chot"),
        "total_students": total_students,
        "present": present_count,
        "late": late_count,
        "excused": excused_count,
        "unexcused": unexcused_count,
        "pending": counts[AttendanceStatus.PENDING_REVIEW],
        "invalid": counts[AttendanceStatus.INVALID],
        "early_leave": counts[AttendanceStatus.EARLY_LEAVE],
        "attendance_rate": round(attendance_rate, 2),
        "weighted_score_rate": round(weighted_score_rate, 2),
        "records": records,
    }
