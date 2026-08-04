"""
Mobile Attendance & Checkin API routes.
"""

import os
import base64
from datetime import datetime, timedelta
from flask import request, jsonify, session
from werkzeug.security import generate_password_hash
from db.connection import execute_one, execute_query, execute_update
from config import Config
from services import attendance_service
from . import api_mobile_bp
from .helpers import (
    _save_evidence_image,
    _save_multipart_image,
    _is_within_checkin_window,
    _require_mobile_auth,
    calculate_distance,
    verify_nonce,
    limiter,
)


@api_mobile_bp.route("/checkin", methods=["POST"])
@limiter.limit("30 per minute")
def mobile_checkin():
    """
    Check-in từ mobile.
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()

    # === ANTI-REPLAY CHECK ===
    nonce = data.get("nonce")
    timestamp_ms = data.get("timestamp")

    role = payload.get("role", "admin")
    if role == "student" and (not nonce or not timestamp_ms):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Thiếu thông tin chữ ký xác thực (nonce/timestamp)",
                }
            ),
            400,
        )

    if nonce and timestamp_ms:
        is_valid, err_msg = verify_nonce(nonce, timestamp_ms, max_age_seconds=15)
        if not is_valid:
            user_id = payload.get("sub")
            if user_id:
                execute_update(
                    "INSERT INTO gian_lan_log (sinh_vien_id, loai_gian_lan, chi_tiet) VALUES (%s, %s, %s)",
                    (user_id, "Replay Attack", err_msg),
                )
            return jsonify({"success": False, "message": err_msg}), 403

    mssv = (data.get("mssv") or "").strip()
    lop_id = data.get("lop_id")
    session_id = data.get("session_id")  # ID phiên điểm danh (bắt buộc)
    # Server tự tính confidence và trạng thái — không tin app
    camera_id = int(data.get("camera_id") or 0)
    image_base64 = data.get("image_base64")
    session_start = data.get("session_start")
    lat = data.get("lat")
    lng = data.get("lng")

    # === BẢO MẬT: Sinh viên chỉ được điểm danh cho chính mình ===
    if role == "student":
        student_mssv = payload.get("username")  # MSSV của SV đang đăng nhập
        if not mssv:
            mssv = student_mssv  # Tự động điền MSSV nếu không gửi
        elif mssv != student_mssv:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Bạn chỉ được điểm danh cho chính mình!",
                    }
                ),
                403,
            )

    # === Kiểm tra phiên điểm danh đang mở ===
    if session_id:
        session_row = execute_one(
            "SELECT * FROM phien_diem_danh WHERE id = %s AND trang_thai = 1",
            (session_id,),
        )
        if not session_row:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Phiên điểm danh không tồn tại hoặc đã đóng",
                    }
                ),
                403,
            )
        lop_id = session_row["lop_id"]  # Gắn lop_id từ phiên

        # Kiểm tra hết hạn
        if session_row.get("het_han"):
            if datetime.now() > session_row["het_han"]:
                execute_update(
                    "UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = GETDATE() WHERE id = %s",
                    (session_id,),
                )
                return (
                    jsonify(
                        {"success": False, "message": "Phiên điểm danh đã hết hạn"}
                    ),
                    403,
                )
    elif lop_id:
        from services.attendance_session_service import AttendanceSessionService

        session_row = AttendanceSessionService.get_active_session(lop_id=lop_id)
        if not session_row:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Lớp này chưa mở phiên điểm danh. Vui lòng chờ Admin mở.",
                    }
                ),
                403,
            )
        session_id = session_row["id"]
    else:
        return (
            jsonify({"success": False, "message": "Thiếu session_id hoặc lop_id"}),
            400,
        )

    # === KIỂM TRA GPS (Geofencing) ===
    if role == "student":
        if lat is None or lng is None:
            return (
                jsonify(
                    {"success": False, "message": "Thiếu vị trí GPS khi điểm danh"}
                ),
                400,
            )

        classroom = execute_one(
            "SELECT latitude, longitude, radius FROM lop_hoc WHERE id = %s", (lop_id,)
        )
        if classroom and classroom.get("latitude") and classroom.get("longitude"):
            dist = calculate_distance(
                float(lat), float(lng), classroom["latitude"], classroom["longitude"]
            )
            radius = classroom.get("radius") or 100
            if dist > radius:
                execute_update(
                    "INSERT INTO gian_lan_log (sinh_vien_id, loai_gian_lan, chi_tiet) VALUES (%s, %s, %s)",
                    (
                        payload.get("sub"),
                        "Fake GPS",
                        f"Khoảng cách: {dist:.1f}m (cho phép {radius}m). Tọa độ SV: {lat},{lng}",
                    ),
                )
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": f"Bạn đang ở ngoài phạm vi lớp học ({dist:.1f}m)! Vui lòng di chuyển vào lớp.",
                        }
                    ),
                    403,
                )

    if session_start == "auto" or not session_start:
        from services.class_service import get_class_start_time

        session_start = get_class_start_time(lop_id)

    in_window, window_error = _is_within_checkin_window(session_start)
    if not in_window:
        return jsonify({"success": False, "message": window_error}), 403

    if not mssv:
        return jsonify({"success": False, "message": "Thiếu MSSV"}), 400

    sv = execute_one("SELECT id, is_locked FROM sinh_vien WHERE mssv = %s", (mssv,))
    if not sv:
        return jsonify({"success": False, "message": "Không tìm thấy sinh viên"}), 404

    if sv.get("is_locked") == 1:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Tài khoản của bạn đã bị khóa do vi phạm quy chế. Vui lòng liên hệ Admin.",
                }
            ),
            403,
        )

    evidence_path = None
    upload_image = request.files.get("image")
    if image_base64:
        try:
            evidence_path = _save_evidence_image(image_base64, mssv)
        except Exception as e:
            return (
                jsonify(
                    {"success": False, "message": f"Lưu ảnh bằng chứng thất bại: {e}"}
                ),
                400,
            )
    elif upload_image:
        try:
            evidence_path = _save_multipart_image(upload_image, mssv)
        except Exception as e:
            return (
                jsonify({"success": False, "message": f"Lưu ảnh upload thất bại: {e}"}),
                400,
            )

    log_result = attendance_service.record_attendance(
        session_id=session_id,
        student_id=sv["id"],
        method="MOBILE_GPS",
        evidence_path=evidence_path,
        latitude=lat,
        longitude=lng,
        camera_id=camera_id,
    )

    if not log_result or not log_result.get("success"):
        error_msg = (
            log_result.get("message", "Check-in bị bỏ qua")
            if log_result
            else "Check-in thất bại"
        )
        error_code = (
            log_result.get("error_code", "UNKNOWN") if log_result else "UNKNOWN"
        )
        status_code = 409 if error_code in ("DUPLICATE_EVENT",) else 400
        if log_result and log_result.get("action") == "observed":
            # Đã điểm danh rồi — trả về thành công
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Sinh viên đã điểm danh trong phiên này",
                        "data": {
                            "mssv": mssv,
                            "action": "observed",
                            "status": log_result.get("status", "PRESENT"),
                            "display_status": log_result.get(
                                "display_status", "Có mặt"
                            ),
                            "late_minutes": log_result.get("late_minutes", 0),
                        },
                    }
                ),
                200,
            )
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": error_code, "message": error_msg},
                    "message": error_msg,
                }
            ),
            status_code,
        )

    return (
        jsonify(
            {
                "success": True,
                "message": "Ghi nhận điểm danh thành công",
                "data": {
                    "mssv": mssv,
                    "action": log_result.get("action"),
                    "status": log_result.get("status", "PRESENT"),
                    "display_status": log_result.get("display_status", "Có mặt"),
                    "late_minutes": log_result.get("late_minutes", 0),
                    "evidence_path": evidence_path,
                },
            }
        ),
        200,
    )


@api_mobile_bp.route("/checkout", methods=["POST"])
def mobile_checkout():
    """
    Checkout riêng cho mobile app.
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}

    # === ANTI-REPLAY CHECK ===
    nonce = data.get("nonce")
    timestamp_ms = data.get("timestamp")

    if nonce and timestamp_ms:
        is_valid, err_msg = verify_nonce(nonce, timestamp_ms, max_age_seconds=15)
        if not is_valid:
            user_id = payload.get("sub")
            if user_id:
                execute_update(
                    "INSERT INTO gian_lan_log (sinh_vien_id, loai_gian_lan, chi_tiet) VALUES (%s, %s, %s)",
                    (user_id, "Replay Attack", err_msg),
                )
            return jsonify({"success": False, "message": err_msg}), 403

    mssv = (data.get("mssv") or "").strip()
    lop_id = data.get("lop_id")
    camera_id = int(data.get("camera_id") or 0)
    image_base64 = data.get("image_base64")

    if not mssv:
        return jsonify({"success": False, "message": "Thiếu MSSV"}), 400
    if lop_id is None:
        return jsonify({"success": False, "message": "Thiếu lop_id"}), 400

    evidence_path = None
    if image_base64:
        try:
            evidence_path = _save_evidence_image(image_base64, mssv)
        except Exception as e:
            return (
                jsonify(
                    {"success": False, "message": f"Lưu ảnh bằng chứng thất bại: {e}"}
                ),
                400,
            )

    result = attendance_service.mobile_checkout(
        mssv=mssv, lop_id=lop_id, camera_id=camera_id
    )
    if not result.get("success"):
        return (
            jsonify(
                {
                    "success": False,
                    "message": result.get("message", "Checkout thất bại"),
                }
            ),
            409,
        )

    if evidence_path:
        sv = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,))
        if sv:
            execute_update(
                "WITH cte AS (SELECT TOP 1 * FROM diem_danh WHERE sinh_vien_id = %s AND lop_id = %s AND CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE) ORDER BY id DESC) UPDATE cte SET ghi_chu = %s",
                (sv["id"], lop_id, f"EVIDENCE:{evidence_path}"),
            )

    return (
        jsonify(
            {
                "success": True,
                "message": "Checkout thành công",
                "data": {
                    "mssv": mssv,
                    "lop_id": lop_id,
                    "evidence_path": evidence_path,
                },
            }
        ),
        200,
    )


@api_mobile_bp.route("/stats", methods=["GET"])
def get_stats():
    """
    Lấy thống kê điểm danh trong ngày cho màn hình chính
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        if payload.get("role") == "student":
            user_id = payload.get("sub")

            lop_row = execute_one(
                "SELECT lop_id FROM sinh_vien WHERE id = %s", (user_id,)
            )
            lop_id = lop_row["lop_id"] if lop_row else 0

            total_sessions_row = execute_one(
                "SELECT COUNT(*) as count FROM phien_diem_danh WHERE lop_id = %s AND (trang_thai = 0 OR is_cancelled = 0)",
                (lop_id,),
            )
            total_sessions = total_sessions_row["count"] if total_sessions_row else 0

            present_row = execute_one(
                "SELECT COUNT(*) as count FROM diem_danh WHERE sinh_vien_id = %s AND status = 'PRESENT'",
                (user_id,),
            )
            present_sv = present_row["count"] if present_row else 0

            late_row = execute_one(
                "SELECT COUNT(*) as count FROM diem_danh WHERE sinh_vien_id = %s AND status = 'LATE'",
                (user_id,),
            )
            late_sv = late_row["count"] if late_row else 0

            absent_sv = (
                total_sessions - present_sv - late_sv
                if total_sessions > (present_sv + late_sv)
                else 0
            )
            attendance_rate = (
                ((present_sv + late_sv) / total_sessions * 100)
                if total_sessions > 0
                else 0
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "data": {
                            "total": total_sessions,
                            "present": present_sv,
                            "late": late_sv,
                            "absent": absent_sv,
                            "rate": round(attendance_rate, 1),
                            "date": today_str,
                        },
                    }
                ),
                200,
            )

        total_sv_row = execute_one("SELECT COUNT(*) as count FROM sinh_vien")
        present_sv_row = execute_one(
            "SELECT COUNT(DISTINCT sinh_vien_id) as count FROM diem_danh WHERE CAST(thoi_gian AS DATE) = CAST(GETDATE() AS DATE) AND status IN ('PRESENT', 'LATE')"
        )
        total_sv = total_sv_row["count"] if total_sv_row else 0
        present_sv = present_sv_row["count"] if present_sv_row else 0
        absent_sv = total_sv - present_sv if total_sv > present_sv else 0

        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "total": total_sv,
                        "present": present_sv,
                        "absent": absent_sv,
                        "date": today_str,
                    },
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/history", methods=["GET"])
def get_history():
    """
    Lấy danh sách điểm danh gần đây
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    limit = request.args.get("limit", 200, type=int)
    mssv_query = request.args.get("mssv")
    lop_id = request.args.get("lop_id", type=int)
    date_query = request.args.get("date")  # YYYY-MM-DD
    month_query = request.args.get("month", type=int)
    year_query = request.args.get("year", type=int)

    if payload and payload.get("role") == "student":
        mssv_query = payload.get("username")

    try:
        sql = """
            SELECT dd.id, dd.thoi_gian, dd.gio_ra, dd.trang_thai, dd.do_chinh_xac, dd.ghi_chu,
                   dd.anh_checkin, dd.anh_checkout, sv.ho_ten, sv.mssv, sv.avatar, l.ma_lop 
            FROM diem_danh dd
            JOIN sinh_vien sv ON dd.sinh_vien_id = sv.id
            LEFT JOIN lop_hoc l ON dd.lop_id = l.id
            WHERE (@mssv IS NULL OR sv.mssv = @mssv)
              AND (@lop_id IS NULL OR l.id = @lop_id)
              AND (@date IS NULL OR CAST(dd.thoi_gian AS DATE) = @date)
              AND (@month IS NULL OR MONTH(dd.thoi_gian) = @month)
              AND (@year IS NULL OR YEAR(dd.thoi_gian) = @year)
            ORDER BY dd.thoi_gian DESC
            OFFSET 0 ROWS FETCH NEXT @limit ROWS ONLY
        """
        params = {
            "mssv": mssv_query,
            "lop_id": lop_id,
            "date": date_query,
            "month": month_query,
            "year": year_query,
            "limit": limit,
        }
        records = execute_query(sql, params)

        for row in records:
            if "thoi_gian" in row and row["thoi_gian"]:
                row["thoi_gian"] = row["thoi_gian"].strftime("%Y-%m-%d %H:%M:%S")
            if "gio_ra" in row and row["gio_ra"]:
                row["gio_ra"] = row["gio_ra"].strftime("%Y-%m-%d %H:%M:%S")

            note = row.get("ghi_chu") or ""
            if note.startswith("EVIDENCE:"):
                row["evidence_path"] = note.replace("EVIDENCE:", "", 1)
            else:
                row["evidence_path"] = None

        return jsonify({"success": True, "data": records}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/attendance/<int:record_id>", methods=["DELETE"])
def delete_attendance_record(record_id):
    """
    Hủy (soft-delete) 1 bản ghi điểm danh. Bắt buộc nhập lý do.
    Ghi audit log.
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get("role") == "student":
            return (
                jsonify(
                    {"success": False, "message": "Chỉ Admin mới được hủy bản ghi"}
                ),
                403,
            )

        data = request.get_json(silent=True) or {}
        reason = (data.get("reason") or "").strip()
        if not reason:
            return (
                jsonify(
                    {"success": False, "message": "Bắt buộc nhập lý do khi hủy bản ghi"}
                ),
                400,
            )

        from services.attendance_session_service import AttendanceSessionService
        from services.attendance_policy import AttendanceStatus

        result = AttendanceSessionService.update_attendance_status(
            record_id, AttendanceStatus.INVALID, payload.get("sub"), reason
        )
        return jsonify(result), 200 if result.get("success") else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/attendance/clear", methods=["DELETE"])
def clear_attendance_history():
    """
    [DEPRECATED] Không cho phép xóa toàn bộ lịch sử điểm danh.
    Sử dụng cancel_session hoặc update_attendance_status thay thế.
    """
    return (
        jsonify(
            {
                "success": False,
                "message": "Không được phép xóa toàn bộ dữ liệu điểm danh. Sử dụng hủy phiên hoặc sửa từng bản ghi.",
            }
        ),
        403,
    )


@api_mobile_bp.route("/register_face", methods=["POST"])
def mobile_register_face():
    """
    API để Mobile App đăng ký khuôn mặt học sinh trực tiếp
    """
    data = request.get_json(silent=True) or {}
    mssv = (data.get("mssv") or "").strip()
    ho_ten = (data.get("ho_ten") or "").strip()
    lop_id = data.get("lop_id")
    email = (data.get("email") or "").strip()
    sdt = (data.get("sdt") or "").strip()
    ngay_sinh = data.get("ngay_sinh")
    gioi_tinh = data.get("gioi_tinh")
    if ngay_sinh == "":
        ngay_sinh = None
    if email == "":
        email = None
    if sdt == "":
        sdt = None
    images = data.get("images", [])

    if not mssv or not ho_ten or not lop_id:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Thiếu thông tin bắt buộc (MSSV, Họ Tên, Lớp)",
                }
            ),
            400,
        )

    if not images or len(images) == 0:
        return (
            jsonify(
                {"success": False, "message": "Cần cung cấp ít nhất 1 ảnh khuôn mặt"}
            ),
            400,
        )

    from services import student_service

    sv = execute_one(
        "SELECT id, ho_ten, password_hash FROM sinh_vien WHERE mssv = %s", (mssv,)
    )

    if not sv:
        try:
            default_password = generate_password_hash("123456", method="pbkdf2:sha256")
            new_id = execute_update(
                """INSERT INTO sinh_vien (mssv, ho_ten, lop_id, avatar, password_hash, trang_thai, trang_thai_face, email, sdt, ngay_sinh, gioi_tinh, created_at) 
                   VALUES (%s, %s, %s, %s, %s, 1, 1, %s, %s, %s, %s, GETDATE())""",
                (
                    mssv,
                    ho_ten,
                    lop_id,
                    f"{mssv}/0.jpg",
                    default_password,
                    email,
                    sdt,
                    ngay_sinh,
                    gioi_tinh,
                ),
            )
            sv_id = new_id
        except Exception as e:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Không thể tạo hồ sơ sinh viên mới: {e}",
                    }
                ),
                500,
            )
    else:
        sv_id = sv["id"]
        if ho_ten.lower() != sv["ho_ten"].lower():
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Họ tên không khớp với dữ liệu hệ thống của MSSV này",
                    }
                ),
                400,
            )

        update_data = {
            "avatar": f"{mssv}/0.jpg",
            "trang_thai_face": 1,
            "email": email,
            "sdt": sdt,
            "ngay_sinh": ngay_sinh,
            "gioi_tinh": gioi_tinh,
        }

        if not sv.get("password_hash"):
            update_data["password_hash"] = generate_password_hash(
                "123456", method="pbkdf2:sha256"
            )

        student_service.update(sv_id, update_data)

    student_dir = os.path.join(Config.DATABASE_DIR, mssv)
    os.makedirs(student_dir, exist_ok=True)

    saved_count = 0
    for idx, b64 in enumerate(images):
        try:
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            img_data = base64.b64decode(b64.strip())
            with open(os.path.join(student_dir, f"{idx}.jpg"), "wb") as f:
                f.write(img_data)
            saved_count += 1
        except Exception:
            pass

    return (
        jsonify(
            {
                "success": True,
                "message": f"Đã đăng ký tài khoản và lưu thành công {saved_count} ảnh khuôn mặt.",
                "data": {"mssv": mssv, "images_saved": saved_count},
            }
        ),
        200,
    )


@api_mobile_bp.route("/pending-faces", methods=["GET"])
def get_pending_faces():
    """
    Lấy danh sách sinh viên đang chờ duyệt khuôn mặt
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error or payload.get("role") != "admin":
        return jsonify({"success": False, "message": "Quyền truy cập bị từ chối"}), 403

    try:
        sql = """
            SELECT sv.id, sv.mssv, sv.ho_ten, sv.avatar, lh.ma_lop 
            FROM sinh_vien sv
            LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
            WHERE sv.trang_thai_face = 1
        """
        records = execute_query(sql)
        return jsonify({"success": True, "data": records}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/approve-face", methods=["POST"])
def approve_face():
    """
    Phê duyệt hoặc từ chối khuôn mặt sinh viên
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error or payload.get("role") != "admin":
        return jsonify({"success": False, "message": "Quyền truy cập bị từ chối"}), 403

    data = request.get_json(silent=True) or {}
    sv_id = data.get("id")
    status = data.get("status")  # 2: Approved, 3: Rejected

    if not sv_id or status not in [2, 3]:
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ"}), 400

    try:
        execute_update(
            "UPDATE sinh_vien SET trang_thai_face = %s WHERE id = %s", (status, sv_id)
        )
        msg = "Đã duyệt khuôn mặt" if status == 2 else "Đã từ chối khuôn mặt"
        return jsonify({"success": True, "message": msg}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/face-gallery", methods=["GET"])
def get_face_gallery():
    """
    Lấy danh sách các ảnh khuôn mặt đã đăng ký của sinh viên
    """
    payload, auth_error = _require_mobile_auth()

    if auth_error and not session.get("admin_id"):
        return auth_error

    role = payload.get("role") if payload else "admin"
    user_id = payload.get("sub") if payload else session.get("admin_id")

    if role == "student":
        user = execute_one("SELECT mssv FROM sinh_vien WHERE id = %s", (user_id,))
        if not user:
            return (
                jsonify({"success": False, "message": "Không tìm thấy sinh viên"}),
                404,
            )
        mssv = user["mssv"]
    else:
        mssv = request.args.get("mssv")
        if not mssv:
            return jsonify({"success": False, "message": "Thiếu MSSV"}), 400

    student_dir = os.path.join(Config.DATABASE_DIR, mssv)
    if not os.path.exists(student_dir):
        return jsonify({"success": True, "data": []}), 200

    try:
        images = [
            f
            for f in os.listdir(student_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        image_urls = [f"{mssv}/{img}" for img in images]

        return jsonify({"success": True, "data": image_urls}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/student/checkin", methods=["POST"])
@limiter.limit("30 per minute")
def student_self_checkin():
    """
    API đặc biệt cho sinh viên tự điểm danh bằng khuôn mặt.
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    if payload.get("role") != "student":
        return (
            jsonify({"success": False, "message": "API này chỉ dành cho sinh viên"}),
            403,
        )

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    image_base64 = data.get("image_base64")
    sv_lat = data.get("vi_do")
    sv_lng = data.get("kinh_do")

    if not session_id:
        return jsonify({"success": False, "message": "Thiếu session_id"}), 400
    if not image_base64:
        return jsonify({"success": False, "message": "Thiếu ảnh khuôn mặt"}), 400

    student_mssv = payload.get("username")
    student_id = payload.get("sub")

    session_row = execute_one(
        "SELECT * FROM phien_diem_danh WHERE id = %s AND trang_thai = 1", (session_id,)
    )
    if not session_row:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Phiên điểm danh không tồn tại hoặc đã đóng",
                }
            ),
            403,
        )

    if session_row.get("het_han") and datetime.now() > session_row["het_han"]:
        execute_update(
            "UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = GETDATE() WHERE id = %s",
            (session_id,),
        )
        return jsonify({"success": False, "message": "Phiên điểm danh đã hết hạn"}), 403

    if session_row.get("vi_do") is not None and session_row.get("kinh_do") is not None:
        if sv_lat is None or sv_lng is None:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Hệ thống yêu cầu quyền truy cập vị trí để xác minh bạn đang ở lớp học.",
                    }
                ),
                400,
            )

        distance = calculate_distance(
            sv_lat, sv_lng, session_row["vi_do"], session_row["kinh_do"]
        )
        max_radius = 50

        if distance > max_radius:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"Bạn đang ở quá xa lớp học ({int(distance)}m). Vui lòng đến lớp để điểm danh.",
                    }
                ),
                403,
            )

    lop_id = session_row["lop_id"]

    sv = execute_one(
        "SELECT id, lop_id, ho_ten FROM sinh_vien WHERE mssv = %s", (student_mssv,)
    )
    if not sv:
        return (
            jsonify(
                {"success": False, "message": "Không tìm thấy thông tin sinh viên"}
            ),
            404,
        )

    from routes.public import _do_recognize

    recognize_result = _do_recognize(image_base64)

    if not recognize_result or not recognize_result.get("success"):
        return (
            jsonify(
                {
                    "success": False,
                    "message": (
                        recognize_result.get("msg", "Không nhận diện được khuôn mặt")
                        if recognize_result
                        else "Lỗi nhận diện"
                    ),
                }
            ),
            400,
        )

    recognized_mssv = recognize_result.get("student", {}).get("mssv", "")
    if recognized_mssv != student_mssv:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Khuôn mặt không khớp với tài khoản đang đăng nhập! Vui lòng tự quét khuôn mặt của chính bạn.",
                }
            ),
            403,
        )

    evidence_path = None
    try:
        evidence_path = _save_evidence_image(image_base64, student_mssv)
    except Exception:
        pass

    confidence = float(recognize_result.get("student", {}).get("do_chinh_xac", 0.0))
    log_result = attendance_service.record_attendance(
        session_id=session_id,
        student_id=sv["id"],
        method="MOBILE_FACE",
        confidence=confidence,
        evidence_path=evidence_path,
        latitude=sv_lat,
        longitude=sv_lng,
    )

    if not log_result or not log_result.get("success"):
        if log_result and log_result.get("action") == "observed":
            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Bạn đã điểm danh rồi trong phiên này. Xin chào {sv['ho_ten']}",
                        "data": {"mssv": student_mssv, "action": "observed"},
                    }
                ),
                200,
            )
        return (
            jsonify(
                {
                    "success": False,
                    "message": (
                        log_result.get("message", "Điểm danh thất bại")
                        if log_result
                        else "Điểm danh thất bại"
                    ),
                }
            ),
            409,
        )

    try:
        lop_info = execute_one("SELECT ten_lop FROM lop_hoc WHERE id = %s", (lop_id,))
        ten_lop = lop_info["ten_lop"] if lop_info else f"Lớp ID: {lop_id}"
        execute_update(
            "INSERT INTO thong_bao (sinh_vien_id, tieu_de, noi_dung) VALUES (%s, %s, %s)",
            (
                sv["id"],
                "Điểm danh thành công",
                f"Bạn đã điểm danh thành công lớp {ten_lop} vào lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}.",
            ),
        )
    except Exception as e:
        print(f"Lỗi tạo thông báo: {e}")

    return (
        jsonify(
            {
                "success": True,
                "message": f"Điểm danh thành công! Xin chào {sv['ho_ten']}",
                "data": {
                    "mssv": student_mssv,
                    "ho_ten": sv["ho_ten"],
                    "action": log_result.get("action"),
                    "do_chinh_xac": confidence,
                    "evidence_path": evidence_path,
                },
            }
        ),
        200,
    )


@api_mobile_bp.route("/stats/classes", methods=["GET"])
def get_class_stats():
    """
    Lấy tỉ lệ đi học của từng lớp
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error

        sql = """
            SELECT l.id, l.ma_lop, l.ten_lop,
                   (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = l.id AND sv.trang_thai = 1) as tong_sv,
                   (SELECT COUNT(DISTINCT d.sinh_vien_id) FROM diem_danh d 
                    WHERE d.lop_id = l.id AND CAST(d.thoi_gian AS DATE) = CAST(GETDATE() AS DATE)) as so_co_mat_hom_nay
            FROM lop_hoc l
            WHERE l.trang_thai = 1
        """
        results = execute_query(sql)
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/stats/absent-risk", methods=["GET"])
def get_absent_risk():
    """
    Danh sách SV vắng nhiều
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error

        sql = """
            SELECT sv.mssv, sv.ho_ten, l.ma_lop,
                   (SELECT COUNT(*) FROM phien_diem_danh p WHERE p.lop_id = sv.lop_id AND p.trang_thai = 0) as tong_buoi_hoc,
                   (SELECT COUNT(*) FROM diem_danh d WHERE d.sinh_vien_id = sv.id AND d.status IN ('PRESENT', 'LATE')) as so_buoi_di
            FROM sinh_vien sv
            JOIN lop_hoc l ON sv.lop_id = l.id
            WHERE sv.trang_thai = 1
            HAVING (tong_buoi_hoc - so_buoi_di) >= 1
            ORDER BY (tong_buoi_hoc - so_buoi_di) DESC
            LIMIT 20
        """
        results = execute_query(sql)
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/stats/daily-trend", methods=["GET"])
def get_daily_trend():
    """
    Xu hướng điểm danh 7 ngày gần nhất
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error

        sql = """
            SELECT CAST(thoi_gian AS DATE) as ngay, COUNT(*) as so_luong
            FROM diem_danh
            WHERE thoi_gian >= DATEADD(day, -7, CAST(GETDATE() AS DATE))
            GROUP BY CAST(thoi_gian AS DATE)
            ORDER BY ngay ASC
        """
        results = execute_query(sql)
        for r in results:
            if hasattr(r["ngay"], "strftime"):
                r["ngay"] = r["ngay"].strftime("%d/%m")

        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/leave-request", methods=["POST"])
def mobile_leave_request():
    """Sinh viên gửi đơn xin phép"""
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get("role") != "student":
        return (
            jsonify(
                {"success": False, "message": "Chỉ sinh viên mới có quyền gửi đơn"}
            ),
            403,
        )

    sinh_vien_id = payload.get("sub")
    mssv = payload.get("username")

    data = request.get_json(silent=True) or {}
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()

    lop_id = data.get("lop_id")
    session_id = data.get("session_id")
    ly_do = data.get("ly_do")
    image_base64 = data.get("image_base64")
    upload_image = request.files.get("image")

    if not lop_id or not session_id or not ly_do:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Thiếu thông tin lớp, phiên điểm danh hoặc lý do",
                }
            ),
            400,
        )

    from db.connection import execute_one, execute_query

    # Kiểm tra phiên
    session_row = execute_one(
        "SELECT * FROM phien_diem_danh WHERE id = %s AND lop_id = %s",
        (session_id, lop_id),
    )
    if not session_row:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Phiên điểm danh không tồn tại cho lớp này",
                }
            ),
            404,
        )

    # Kiểm tra nếu phiên đã đóng và quá hạn xin phép
    if session_row["trang_thai"] == 0:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Phiên điểm danh đã đóng, không thể gửi đơn xin phép nữa",
                }
            ),
            403,
        )

    # Kiểm tra xem sinh viên có thuộc lớp này không
    sv = execute_one(
        "SELECT id FROM sinh_vien WHERE id = %s AND lop_id = %s", (sinh_vien_id, lop_id)
    )
    if not sv:
        return jsonify({"success": False, "message": "Bạn không thuộc lớp này"}), 403

    # Kiểm tra xem đã gửi đơn cho phiên này chưa
    existing = execute_one(
        "SELECT id FROM don_xin_phep WHERE sinh_vien_id = %s AND phien_id = %s",
        (sinh_vien_id, session_id),
    )
    if existing:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Bạn đã gửi đơn xin phép cho phiên này rồi",
                }
            ),
            409,
        )

    minh_chung_url = None
    if image_base64:
        minh_chung_url = _save_evidence_image(image_base64, mssv)
    elif upload_image:
        minh_chung_url = _save_multipart_image(upload_image, mssv)

    from services.leave_service import create_leave_request

    res = create_leave_request(sinh_vien_id, lop_id, session_id, ly_do, minh_chung_url)
    if res > 0:
        return jsonify({"success": True, "message": "Gửi đơn xin phép thành công"}), 200
    return jsonify({"success": False, "message": "Gửi đơn thất bại"}), 500


@api_mobile_bp.route("/my-leave-requests", methods=["GET"])
def mobile_my_leave_requests():
    """Lấy danh sách đơn xin phép của sinh viên"""
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get("role") != "student":
        return jsonify({"success": False, "message": "Chỉ sinh viên mới xem được"}), 403

    sinh_vien_id = payload.get("sub")
    from services.leave_service import get_student_leave_requests

    reqs = get_student_leave_requests(sinh_vien_id)

    for r in reqs:
        if r.get("thoi_gian_tao"):
            r["thoi_gian_tao"] = r["thoi_gian_tao"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({"success": True, "data": reqs}), 200
