"""
Mobile Sessions API routes.
"""

import threading
from datetime import datetime, timedelta
from flask import request, jsonify
from db.connection import execute_one, execute_query, execute_update
from services.telegram_alert import send_telegram_message
from . import api_mobile_bp
from .helpers import _require_mobile_auth


@api_mobile_bp.route("/sessions/create", methods=["POST"])
def create_session():
    """
    Admin tạo phiên điểm danh cho một lớp. Sinh viên sẽ thấy phiên này trên mobile.
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get("role") == "student":
        return (
            jsonify(
                {"success": False, "message": "Chỉ Admin mới được tạo phiên điểm danh"}
            ),
            403,
        )

    data = request.get_json(silent=True) or {}
    lop_id = data.get("lop_id")
    mo_ta = data.get("mo_ta", "")
    duration_minutes = int(data.get("duration_minutes") or 90)

    if not lop_id:
        return jsonify({"success": False, "message": "Thiếu lop_id"}), 400

    lop = execute_one(
        "SELECT id, ma_lop, ten_lop FROM lop_hoc WHERE id = %s AND trang_thai = 1",
        (lop_id,),
    )
    if not lop:
        return (
            jsonify(
                {"success": False, "message": "Lớp không tồn tại hoặc đã vô hiệu hóa"}
            ),
            404,
        )

    from services.attendance_session_service import AttendanceSessionService

    session_info, error = AttendanceSessionService.create_session(
        lop_id=lop_id,
        admin_id=payload.get("sub"),
        loai_phien="MOBILE",
        mo_ta=mo_ta,
        gio_hoc_du_kien=datetime.now(),
        mo_checkin=None,
        dong_checkin=None,
        het_han=datetime.now() + timedelta(minutes=duration_minutes),
        vi_do=data.get("vi_do"),
        kinh_do=data.get("kinh_do"),
        radius=100,
        require_gps=False,
    )
    if error:
        return jsonify({"success": False, "message": error}), 400

    new_id = session_info["id"]

    def _notify_students():
        try:
            students = execute_query(
                "SELECT id, fcm_token FROM sinh_vien WHERE lop_id = %s AND trang_thai = 1",
                (lop_id,),
            )

            title = f"📢 Điểm danh: {lop['ma_lop']}"
            body = f"Phiên điểm danh lớp {lop['ten_lop']} đã mở! Thời hạn: {duration_minutes} phút."

            for sv in students:
                execute_update(
                    "INSERT INTO thong_bao (sinh_vien_id, tieu_de, noi_dung) VALUES (%s, %s, %s)",
                    (sv["id"], title, body),
                )

                if sv.get("fcm_token"):
                    try:
                        from services.fcm_service import send_push_notification

                        send_push_notification(
                            sv["fcm_token"],
                            title,
                            body,
                            data={
                                "type": "session_opened",
                                "session_id": str(new_id),
                                "lop_id": str(lop_id),
                            },
                        )
                    except Exception:
                        pass

            print(
                f"[SESSION] Đã gửi thông báo cho {len(students)} sinh viên lớp {lop['ma_lop']}"
            )
        except Exception as e:
            print(f"[SESSION] Lỗi gửi thông báo: {e}")

    threading.Thread(target=_notify_students, daemon=True).start()

    return (
        jsonify(
            {
                "success": True,
                "message": f"Đã mở phiên điểm danh cho lớp {lop['ma_lop']}",
                "data": {
                    "session_id": new_id,
                    "lop_id": lop_id,
                    "ma_lop": lop["ma_lop"],
                    "ten_lop": lop["ten_lop"],
                    "het_han": (
                        session_info.get(
                            "het_han",
                            datetime.now() + timedelta(minutes=duration_minutes),
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        if hasattr(session_info.get("het_han"), "strftime")
                        else str(session_info.get("het_han"))
                    ),
                    "duration_minutes": duration_minutes,
                },
            }
        ),
        200,
    )


@api_mobile_bp.route("/sessions/active", methods=["GET"])
def get_active_sessions():
    """
    Lấy danh sách các phiên điểm danh đang mở.
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    role = payload.get("role", "admin")
    user_id = payload.get("sub")

    try:
        execute_update(
            "UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = GETDATE() WHERE trang_thai = 1 AND het_han IS NOT NULL AND het_han < GETDATE()"
        )

        if role == "student":
            student = execute_one(
                "SELECT lop_id, mssv FROM sinh_vien WHERE id = %s", (user_id,)
            )
            student_mssv = student["mssv"] if student else ""

            sql = """
                SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.het_han,
                       l.ma_lop, l.ten_lop, l.giao_vien,
                       (SELECT COUNT(*) FROM diem_danh d 
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND d.status IN ('PRESENT', 'LATE')) as so_da_diem_danh,
                       (SELECT COUNT(*) FROM diem_danh d 
                        JOIN sinh_vien sv2 ON d.sinh_vien_id = sv2.id
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND sv2.mssv = %s) as da_diem_danh_chua
                FROM phien_diem_danh p
                JOIN lop_hoc l ON p.lop_id = l.id
                WHERE p.trang_thai = 1
                ORDER BY p.bat_dau DESC
            """
            sessions = execute_query(sql, (student_mssv,))
        else:
            sql = """
                SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.het_han,
                       l.ma_lop, l.ten_lop, l.giao_vien,
                       (SELECT COUNT(DISTINCT d.sinh_vien_id) FROM diem_danh d
                        WHERE d.phien_id = p.id
                        AND d.status IN ('PRESENT', 'LATE')) as so_da_diem_danh,
                       (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = p.lop_id AND sv.trang_thai = 1) as tong_sv
                FROM phien_diem_danh p
                JOIN lop_hoc l ON p.lop_id = l.id
                WHERE p.trang_thai = 1 AND ISNULL(p.is_cancelled, 0) = 0
                ORDER BY p.bat_dau DESC
            """
            sessions = execute_query(sql)

        for s in sessions:
            if s.get("bat_dau"):
                s["bat_dau"] = s["bat_dau"].strftime("%Y-%m-%d %H:%M:%S")
            if s.get("het_han"):
                s["het_han"] = s["het_han"].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({"success": True, "data": sessions}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/sessions/<int:session_id>/stop", methods=["POST"])
def stop_session_api(session_id):
    """Admin đóng phiên điểm danh."""
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get("role") == "student":
        return (
            jsonify({"success": False, "message": "Chỉ Admin mới được đóng phiên"}),
            403,
        )

    from services.attendance_session_service import AttendanceSessionService

    result = AttendanceSessionService.close_session(
        session_id, admin_id=payload.get("sub")
    )
    if not result.get("success"):
        return jsonify(result), 400

    try:
        summary = result.get("summary", {})
        msg = (
            f"🔔 <b>THÔNG BÁO KẾT THÚC ĐIỂM DANH</b>\n"
            f"--------------------------------\n"
            f"🏫 <b>Phiên:</b> #{session_id}\n"
            f"✅ <b>Có mặt:</b> {summary.get('present', 0)} | <b>Muộn:</b> {summary.get('late', 0)}\n"
            f"📋 <b>Vắng có phép:</b> {summary.get('excused', 0)}\n"
            f"❌ <b>Vắng không phép:</b> {summary.get('unexcused', 0)}\n"
            f"📝 <b>Sĩ số chốt:</b> {summary.get('total_students', 0)}\n"
        )
        send_telegram_message(msg)
    except Exception as e:
        print(f"Lỗi gửi thông báo Telegram: {e}")

    return (
        jsonify(
            {
                "success": True,
                "message": "Đã đóng phiên điểm danh và tổng hợp báo cáo",
                "data": result,
            }
        ),
        200,
    )


@api_mobile_bp.route("/sessions/<int:session_id>/details", methods=["GET"])
def get_session_details(session_id):
    """
    /sessions/<int:session_id>/details
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get("role") == "student":
            return (
                jsonify(
                    {"success": False, "message": "Chỉ Admin mới được xem chi tiết"}
                ),
                403,
            )

        session_row = execute_one(
            "SELECT p.*, l.ten_lop, l.ma_lop FROM phien_diem_danh p JOIN lop_hoc l ON p.lop_id = l.id WHERE p.id = %s",
            (session_id,),
        )
        if not session_row:
            return jsonify({"success": False, "message": "Phiên không tồn tại"}), 404

        lop_id = session_row["lop_id"]

        sql = """
            SELECT sv.id, sv.mssv, sv.ho_ten, sv.avatar,
                   d.thoi_gian, d.trang_thai, d.status, d.late_minutes, d.ghi_chu
            FROM sinh_vien sv
            LEFT JOIN diem_danh d ON sv.id = d.sinh_vien_id 
                  AND d.phien_id = %s
            WHERE sv.lop_id = %s AND sv.trang_thai = 1
            ORDER BY sv.mssv ASC
        """
        students = execute_query(sql, (session_id, lop_id))

        for s in students:
            if s.get("thoi_gian") and hasattr(s["thoi_gian"], "strftime"):
                s["thoi_gian"] = s["thoi_gian"].strftime("%H:%M:%S")

        bat_dau_str = (
            session_row["bat_dau"].strftime("%Y-%m-%d %H:%M:%S")
            if session_row.get("bat_dau")
            and hasattr(session_row["bat_dau"], "strftime")
            else str(session_row.get("bat_dau"))
        )

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "session": {
                            "id": session_row["id"],
                            "ten_lop": session_row["ten_lop"],
                            "ma_lop": session_row["ma_lop"],
                            "bat_dau": bat_dau_str,
                            "trang_thai": session_row["trang_thai"],
                        },
                        "students": students,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/sessions/history", methods=["GET"])
def get_session_history():
    """
    Lấy lịch sử phiên điểm danh đã đóng
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get("role") == "student":
            return jsonify({"success": False, "message": "Chỉ Admin mới được xem"}), 403

        sql = """
            SELECT TOP 100 p.id, p.lop_id, p.mo_ta, p.bat_dau, p.ket_thuc, p.het_han,
                   l.ma_lop, l.ten_lop, l.giao_vien,
                   (SELECT COUNT(*) FROM diem_danh d 
                    WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                    AND (p.ket_thuc IS NULL OR d.thoi_gian <= p.ket_thuc)
                    AND d.status IN ('PRESENT', 'LATE')) as so_da_diem_danh,
                   (SELECT COUNT(*) FROM sinh_vien sv 
                    WHERE sv.lop_id = p.lop_id AND sv.trang_thai = 1) as tong_sv
            FROM phien_diem_danh p
            JOIN lop_hoc l ON p.lop_id = l.id
            WHERE p.trang_thai = 0
            ORDER BY p.bat_dau DESC
        """
        sessions = execute_query(sql)

        for s in sessions:
            for key in ["bat_dau", "ket_thuc", "het_han"]:
                if s.get(key) and hasattr(s[key], "strftime"):
                    s[key] = s[key].strftime("%Y-%m-%d %H:%M:%S")

        return jsonify({"success": True, "data": sessions}), 200
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    """
    Hủy phiên điểm danh (soft-cancel). Không xóa cứng.
    Bắt buộc nhập lý do hủy.
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get("role") == "student":
            return (
                jsonify({"success": False, "message": "Chỉ Admin mới được hủy phiên"}),
                403,
            )

        data = request.get_json(silent=True) or {}
        reason = (data.get("reason") or "").strip() or "Admin hủy phiên từ mobile"

        from services.attendance_session_service import AttendanceSessionService

        result = AttendanceSessionService.cancel_session(
            session_id, admin_id=payload.get("sub"), reason=reason
        )
        return jsonify(result), 200 if result.get("success") else 400
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500
