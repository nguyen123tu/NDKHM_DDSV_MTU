"""
API Dành cho Mobile App (JSON Responses)
"""

import os
import uuid
import base64
import time
import math
from datetime import datetime, timedelta

import jwt
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from db.connection import execute_one, execute_query, execute_update
from config import Config
from services import attendance_service
from services.telegram_alert import send_telegram_message

# Blueprint sẽ được register trong routes/__init__.py
api_mobile_bp = Blueprint('api_mobile', __name__, url_prefix='/api/mobile')

def calculate_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách (mét) giữa 2 tọa độ GPS bằng công thức Haversine"""
    R = 6371e3
    phi1 = lat1 * math.pi / 180
    phi2 = lat2 * math.pi / 180
    delta_phi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180
    a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _make_token(user, is_student=False):
    """Tạo JWT cho mobile app."""
    payload = {
        "sub": str(user["id"]),
        "username": user["username"] if not is_student else user["mssv"],
        "role": user.get("role", "admin") if not is_student else "student",
        "exp": datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")


def _extract_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def _require_mobile_auth():
    token = _extract_bearer_token()
    if not token:
        return None, (jsonify({"success": False, "message": "Thiếu Bearer token"}), 401)
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, (jsonify({"success": False, "message": "Token đã hết hạn"}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({"success": False, "message": "Token không hợp lệ"}), 401)


def _save_evidence_image(image_b64, mssv):
    """
    Lưu ảnh base64 làm bằng chứng vào database/evidence/YYYYMMDD.
    Trả về relative path để lưu DB.
    """
    if not image_b64:
        return None

    raw = image_b64.strip()
    if "," in raw and raw.startswith("data:image"):
        raw = raw.split(",", 1)[1]

    image_bytes = base64.b64decode(raw)
    date_folder = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join(Config.EVIDENCE_DIR, date_folder)
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{mssv}_{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
    abs_path = os.path.join(save_dir, filename)

    with open(abs_path, "wb") as f:
        f.write(image_bytes)

    rel_path = os.path.relpath(abs_path, Config.BASE_DIR).replace("\\", "/")
    return rel_path


def _save_multipart_image(file_obj, mssv):
    """Lưu ảnh từ multipart/form-data."""
    if file_obj is None:
        return None
    date_folder = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join(Config.EVIDENCE_DIR, date_folder)
    os.makedirs(save_dir, exist_ok=True)
    ext = os.path.splitext(file_obj.filename or "")[-1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    filename = f"{mssv}_{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    abs_path = os.path.join(save_dir, filename)
    file_obj.save(abs_path)
    return os.path.relpath(abs_path, Config.BASE_DIR).replace("\\", "/")


def _is_within_checkin_window(session_start_str):
    """
    session_start_str format: YYYY-mm-dd HH:MM:SS
    Cho phép check-in trong khoảng [start-early, start+late].
    """
    if not session_start_str:
        return True, None
    try:
        start_time = datetime.strptime(session_start_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False, "session_start không đúng định dạng YYYY-mm-dd HH:MM:SS"

    now = datetime.now()
    early = timedelta(minutes=Config.MOBILE_ALLOWED_CHECKIN_EARLY_MIN)
    late = timedelta(minutes=Config.MOBILE_ALLOWED_CHECKIN_LATE_MIN)
    if now < (start_time - early) or now > (start_time + late):
        return False, "Ngoài khung giờ check-in cho phép"
    return True, None

@api_mobile_bp.route('/login', methods=['POST'])
def mobile_login():
    """
    API Đăng nhập cho ứng dụng di động
    ---
    tags:
      - Mobile App API
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: "admin"
            password:
              type: string
              example: "123456"
    responses:
      200:
        description: Đăng nhập thành công
      400:
        description: Thiếu dữ liệu đăng nhập
      401:
        description: Sai tài khoản hoặc mật khẩu
    """
    data = request.get_json(silent=True) or {}
    if 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "message": "Thiếu dữ liệu đăng nhập"}), 400
        
    username = data.get('username')
    password = data.get('password')
    device_id = data.get('device_id')
    
    # Query thử bảng admin trước tiên
    admin = execute_one("SELECT * FROM admin WHERE username = %s", (username,))
    if admin and check_password_hash(admin['password_hash'], password):
        token = _make_token(admin, is_student=False)
        return jsonify({
            "success": True,
            "message": "Đăng nhập Admin thành công",
            "token": token,
            "token_type": "Bearer",
            "expires_in_hours": Config.JWT_EXPIRE_HOURS,
            "user": {
                "id": admin['id'],
                "username": admin['username'],
                "role": admin['role'],
                "name": admin['ho_ten']
            }
        }), 200
        
    # Tiếp theo thử bảng sinh_vien
    student = execute_one("SELECT * FROM sinh_vien WHERE mssv = %s AND trang_thai = 1", (username,))
    if student and student['password_hash'] and check_password_hash(student['password_hash'], password):
        # === DEVICE BINDING ===
        if not device_id:
            return jsonify({"success": False, "message": "Thiếu thông tin thiết bị (Device ID). Vui lòng cập nhật App!"}), 400
            
        current_device = student.get('device_id')
        if not current_device or current_device != device_id:
            # Tự động cập nhật thiết bị mới khi đăng nhập ở máy khác (bỏ giới hạn 1 máy)
            execute_update("UPDATE sinh_vien SET device_id = %s WHERE id = %s", (device_id, student['id']))

        token = _make_token(student, is_student=True)
        return jsonify({
            "success": True,
            "message": "Đăng nhập Sinh viên thành công",
            "token": token,
            "token_type": "Bearer",
            "expires_in_hours": Config.JWT_EXPIRE_HOURS,
            "user": {
                "id": student['id'],
                "username": student['mssv'],
                "role": "student",
                "name": student['ho_ten']
            }
        }), 200

    return jsonify({"success": False, "message": "Sai tài khoản hoặc mật khẩu"}), 401


@api_mobile_bp.route('/fcm-token', methods=['POST'])
def update_fcm_token():
    """
    Cập nhật FCM Device Token cho Mobile
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
        
    data = request.get_json(silent=True) or {}
    token = data.get('fcm_token')
    
    if not token:
        return jsonify({"success": False, "message": "Thiếu fcm_token"}), 400
        
    user_id = payload.get('sub')
    role = payload.get('role')
    
    if role == 'student':
        execute_update("UPDATE sinh_vien SET fcm_token = %s WHERE id = %s", (token, user_id))
    else:
        execute_update("UPDATE admin SET fcm_token = %s WHERE id = %s", (token, user_id))
        
    return jsonify({"success": True, "message": "Cập nhật FCM Token thành công"}), 200

@api_mobile_bp.route('/checkin', methods=['POST'])
def mobile_checkin():
    """
    Check-in từ mobile.
    - Nếu là sinh viên: BẮT BUỘC chỉ được điểm danh cho chính mình.
    - Nếu là admin: được điểm danh cho bất kỳ sinh viên nào.
    - Phải có phiên điểm danh đang mở cho lớp đó.
    ---
    tags:
      - Mobile App API
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            mssv:
              type: string
            lop_id:
              type: integer
            session_id:
              type: integer
            trang_thai:
              type: string
              example: "Co mat"
            image_base64:
              type: string
    responses:
      200:
        description: Ghi nhận điểm danh thành công
      403:
        description: Không có quyền điểm danh
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
    mssv = (data.get("mssv") or "").strip()
    lop_id = data.get("lop_id")
    session_id = data.get("session_id")  # ID phiên điểm danh
    do_chinh_xac = float(data.get("do_chinh_xac") or 0.0)
    camera_id = int(data.get("camera_id") or 0)
    trang_thai = (data.get("trang_thai") or "Co mat").strip()
    image_base64 = data.get("image_base64")
    session_start = data.get("session_start")
    lat = data.get("lat")
    lng = data.get("lng")

    # === BẢO MẬT: Sinh viên chỉ được điểm danh cho chính mình ===
    role = payload.get('role', 'admin')
    if role == 'student':
        student_mssv = payload.get('username')  # MSSV của SV đang đăng nhập
        if not mssv:
            mssv = student_mssv  # Tự động điền MSSV nếu không gửi
        elif mssv != student_mssv:
            return jsonify({
                "success": False,
                "message": "Bạn chỉ được điểm danh cho chính mình!"
            }), 403

    # === Kiểm tra phiên điểm danh đang mở ===
    if session_id:
        session = execute_one(
            "SELECT * FROM phien_diem_danh WHERE id = %s AND trang_thai = 1",
            (session_id,)
        )
        if not session:
            return jsonify({"success": False, "message": "Phiên điểm danh không tồn tại hoặc đã đóng"}), 403
        lop_id = session['lop_id']  # Gắn lop_id từ phiên

        # Kiểm tra hết hạn
        if session.get('het_han'):
            if datetime.now() > session['het_han']:
                # Auto-close expired session
                execute_update("UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = NOW() WHERE id = %s", (session_id,))
                return jsonify({"success": False, "message": "Phiên điểm danh đã hết hạn"}), 403
    elif lop_id:
        # Kiểm tra có phiên đang mở cho lớp này không
        session = execute_one(
            "SELECT * FROM phien_diem_danh WHERE lop_id = %s AND trang_thai = 1 ORDER BY bat_dau DESC LIMIT 1",
            (lop_id,)
        )
        if not session:
            return jsonify({"success": False, "message": "Lớp này chưa mở phiên điểm danh. Vui lòng chờ Admin mở."}), 403
    else:
        return jsonify({"success": False, "message": "Thiếu session_id hoặc lop_id"}), 400

    # === KIỂM TRA GPS (Geofencing) ===
    if role == 'student' and lat is not None and lng is not None:
        classroom = execute_one("SELECT latitude, longitude, radius FROM lop_hoc WHERE id = %s", (lop_id,))
        if classroom and classroom.get('latitude') and classroom.get('longitude'):
            dist = calculate_distance(float(lat), float(lng), classroom['latitude'], classroom['longitude'])
            radius = classroom.get('radius') or 100
            if dist > radius:
                # Ghi log gian lận
                execute_update(
                    "INSERT INTO gian_lan_log (sinh_vien_id, loai_gian_lan, chi_tiet) VALUES (%s, %s, %s)",
                    (payload.get('sub'), "Fake GPS", f"Khoảng cách: {dist:.1f}m (cho phép {radius}m). Tọa độ SV: {lat},{lng}")
                )
                return jsonify({
                    "success": False,
                    "message": f"Bạn đang ở ngoài phạm vi lớp học ({dist:.1f}m)! Vui lòng di chuyển vào lớp."
                }), 403

    in_window, window_error = _is_within_checkin_window(session_start)
    if not in_window:
        return jsonify({"success": False, "message": window_error}), 403

    if not mssv:
        return jsonify({"success": False, "message": "Thiếu MSSV"}), 400

    sv = execute_one("SELECT id, is_locked FROM sinh_vien WHERE mssv = %s", (mssv,))
    if not sv:
        return jsonify({"success": False, "message": "Không tìm thấy sinh viên"}), 404
        
    if sv.get('is_locked') == 1:
        return jsonify({"success": False, "message": "Tài khoản của bạn đã bị khóa do vi phạm quy chế. Vui lòng liên hệ Admin."}), 403

    evidence_path = None
    upload_image = request.files.get("image")
    if image_base64:
        try:
            evidence_path = _save_evidence_image(image_base64, mssv)
        except Exception as e:
            return jsonify({"success": False, "message": f"Lưu ảnh bằng chứng thất bại: {e}"}), 400
    elif upload_image:
        try:
            evidence_path = _save_multipart_image(upload_image, mssv)
        except Exception as e:
            return jsonify({"success": False, "message": f"Lưu ảnh upload thất bại: {e}"}), 400

    log_result = attendance_service.log(
        mssv=mssv,
        lop_id=lop_id,
        do_chinh_xac=do_chinh_xac,
        camera_id=camera_id,
        trang_thai=trang_thai,
    )

    if not log_result:
        return jsonify({
            "success": False,
            "message": "Check-in bị bỏ qua (cooldown hoặc đã điểm danh trước đó)",
            "evidence_path": evidence_path
        }), 409

    if evidence_path:
        execute_update(
            "UPDATE diem_danh SET ghi_chu = %s WHERE sinh_vien_id = %s AND lop_id = %s AND DATE(thoi_gian) = CURDATE() ORDER BY id DESC LIMIT 1",
            (f"EVIDENCE:{evidence_path}", sv["id"], lop_id),
        )

    return jsonify({
        "success": True,
        "message": "Ghi nhận điểm danh thành công",
        "data": {
            "mssv": mssv,
            "action": log_result.get("action"),
            "do_chinh_xac": do_chinh_xac,
            "trang_thai": trang_thai,
            "evidence_path": evidence_path
        }
    }), 200


@api_mobile_bp.route('/checkout', methods=['POST'])
def mobile_checkout():
    """
    Checkout riêng cho mobile app.
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    _, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
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
            return jsonify({"success": False, "message": f"Lưu ảnh bằng chứng thất bại: {e}"}), 400

    result = attendance_service.mobile_checkout(mssv=mssv, lop_id=lop_id, camera_id=camera_id)
    if not result.get("success"):
        return jsonify({"success": False, "message": result.get("message", "Checkout thất bại")}), 409

    if evidence_path:
        sv = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,))
        if sv:
            execute_update(
                "UPDATE diem_danh SET ghi_chu = %s WHERE sinh_vien_id = %s AND lop_id = %s AND DATE(thoi_gian) = CURDATE() ORDER BY id DESC LIMIT 1",
                (f"EVIDENCE:{evidence_path}", sv["id"], lop_id),
            )

    return jsonify({
        "success": True,
        "message": "Checkout thành công",
        "data": {
            "mssv": mssv,
            "lop_id": lop_id,
            "evidence_path": evidence_path,
        }
    }), 200


@api_mobile_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Lấy thống kê điểm danh trong ngày cho màn hình chính
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    today_str = datetime.now().strftime('%Y-%m-%d')
    try:
        if payload.get('role') == 'student':
            user_id = payload.get('sub')
            
            lop_row = execute_one("SELECT lop_id FROM sinh_vien WHERE id = %s", (user_id,))
            lop_id = lop_row['lop_id'] if lop_row else 0
            
            total_sessions_row = execute_one(
                "SELECT COUNT(*) as count FROM phien_diem_danh WHERE lop_id = %s AND DATE(bat_dau) = %s", 
                (lop_id, today_str)
            )
            total_sessions = total_sessions_row['count'] if total_sessions_row else 0

            present_row = execute_one(
                "SELECT COUNT(*) as count FROM diem_danh WHERE sinh_vien_id = %s AND DATE(thoi_gian) = %s AND trang_thai = 'Co mat'",
                (user_id, today_str)
            )
            present_sv = present_row['count'] if present_row else 0
            absent_sv = total_sessions - present_sv if total_sessions > present_sv else 0

            return jsonify({
                "success": True,
                "data": {
                    "total": total_sessions,
                    "present": present_sv,
                    "absent": absent_sv,
                    "date": today_str
                }
            }), 200

        total_sv_row = execute_one("SELECT COUNT(*) as count FROM sinh_vien")
        present_sv_row = execute_one(
            "SELECT COUNT(DISTINCT sinh_vien_id) as count FROM diem_danh WHERE DATE(thoi_gian) = %s AND trang_thai = 'Co mat'",
            (today_str,),
        )
        total_sv = total_sv_row['count'] if total_sv_row else 0
        present_sv = present_sv_row['count'] if present_sv_row else 0
        absent_sv = total_sv - present_sv if total_sv > present_sv else 0
        
        return jsonify({
            "success": True,
            "data": {
                "total": total_sv,
                "present": present_sv,
                "absent": absent_sv,
                "date": today_str
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/history', methods=['GET'])
def get_history():
    """
    Lấy danh sách điểm danh gần đây
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    limit = request.args.get('limit', 200, type=int) # Tăng limit để dễ xuất báo cáo
    mssv_query = request.args.get('mssv')
    lop_id = request.args.get('lop_id', type=int)
    date_query = request.args.get('date') # YYYY-MM-DD
    month_query = request.args.get('month', type=int)
    year_query = request.args.get('year', type=int)
    
    # Nếu là sinh viên, CHỈ cho phép xem lịch sử của chính mình
    if payload and payload.get('role') == 'student':
        mssv_query = payload.get('username')
        
    try:
        sql = """
            SELECT dd.id, dd.thoi_gian, dd.trang_thai, dd.do_chinh_xac, dd.ghi_chu,
                   sv.ho_ten, sv.mssv, sv.avatar, l.ma_lop 
            FROM diem_danh dd
            JOIN sinh_vien sv ON dd.sinh_vien_id = sv.id
            LEFT JOIN lop_hoc l ON dd.lop_id = l.id
            WHERE (%s IS NULL OR sv.mssv = %s)
              AND (%s IS NULL OR l.id = %s)
              AND (%s IS NULL OR DATE(dd.thoi_gian) = %s)
              AND (%s IS NULL OR MONTH(dd.thoi_gian) = %s)
              AND (%s IS NULL OR YEAR(dd.thoi_gian) = %s)
            ORDER BY dd.thoi_gian DESC
            LIMIT %s
        """
        params = (
            mssv_query, mssv_query, 
            lop_id, lop_id, 
            date_query, date_query,
            month_query, month_query,
            year_query, year_query,
            limit
        )
        records = execute_query(sql, params)
        
        # Chuyển đổi datetime sang chuỗi để JSON Serializable
        for row in records:
            if 'thoi_gian' in row and row['thoi_gian']:
                row['thoi_gian'] = row['thoi_gian'].strftime("%Y-%m-%d %H:%M:%S")
            note = row.get('ghi_chu') or ""
            if note.startswith("EVIDENCE:"):
                row['evidence_path'] = note.replace("EVIDENCE:", "", 1)
            else:
                row['evidence_path'] = None
                
        return jsonify({"success": True, "data": records}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/attendance/<int:record_id>', methods=['DELETE'])
def delete_attendance_record(record_id):
    """
    Xóa 1 bản ghi điểm danh
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get('role') == 'student':
            return jsonify({"success": False, "message": "Chỉ Admin mới được xóa"}), 403

        record = execute_one("SELECT id FROM diem_danh WHERE id = %s", (record_id,))
        if not record:
            return jsonify({"success": False, "message": "Bản ghi không tồn tại"}), 404

        execute_update("DELETE FROM diem_danh WHERE id = %s", (record_id,))
        return jsonify({"success": True, "message": "Đã xóa bản ghi điểm danh"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/attendance/clear', methods=['DELETE'])
def clear_attendance_history():
    """
    Xóa toàn bộ lịch sử điểm danh
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get('role') == 'student':
            return jsonify({"success": False, "message": "Chỉ Admin mới được xóa"}), 403

        execute_update("DELETE FROM diem_danh")
        return jsonify({"success": True, "message": "Đã xóa toàn bộ lịch sử điểm danh"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/register_face', methods=['POST'])
def mobile_register_face():
    """
    API để Mobile App đăng ký khuôn mặt học sinh trực tiếp (Cho phép khách và sinh viên)
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    # Bỏ yêu cầu Token để sinh viên mới chưa có tài khoản vẫn đăng ký được

    data = request.get_json(silent=True) or {}
    mssv = (data.get("mssv") or "").strip()
    ho_ten = (data.get("ho_ten") or "").strip()
    lop_id = data.get("lop_id")
    images = data.get("images", []) # array base64
    
    if not mssv or not ho_ten or not lop_id:
        return jsonify({"success": False, "message": "Thiếu thông tin bắt buộc (MSSV, Họ Tên, Lớp)"}), 400
        
    if not images or len(images) == 0:
        return jsonify({"success": False, "message": "Cần cung cấp ít nhất 1 ảnh khuôn mặt"}), 400
        
    from services import student_service
    
    # Kiểm tra xem sinh viên có tồn tại trong hệ thống không
    sv = execute_one("SELECT id, ho_ten FROM sinh_vien WHERE mssv = %s", (mssv,))
    
    if not sv:
        # TRƯỜNG HỢP 1: Sinh viên chưa có trong hệ thống -> Tự động đăng ký mới
        print(f"[REGISTRATION] Creating new student record for MSSV: {mssv}")
        try:
            # Tạo mật khẩu mặc định là MSSV hoặc 123456
            default_password = generate_password_hash("123456", method='pbkdf2:sha256')
            
            new_id = execute_update(
                """INSERT INTO sinh_vien (mssv, ho_ten, lop_id, avatar, password_hash, trang_thai, trang_thai_face, created_at) 
                   VALUES (%s, %s, %s, %s, %s, 1, 1, NOW())""",
                (mssv, ho_ten, lop_id, f"{mssv}/0.jpg", default_password)
            )
            sv_id = new_id
        except Exception as e:
            return jsonify({"success": False, "message": f"Không thể tạo hồ sơ sinh viên mới: {e}"}), 500
    else:
        # TRƯỜNG HỢP 2: Sinh viên đã tồn tại -> Cập nhật thông tin và đưa vào trạng thái chờ duyệt
        sv_id = sv['id']
        # Kiểm tra họ tên khớp (không phân biệt hoa thường) để tránh đăng ký nhầm MSSV của người khác
        if ho_ten.lower() != sv['ho_ten'].lower():
            return jsonify({"success": False, "message": "Họ tên không khớp với dữ liệu hệ thống của MSSV này"}), 400
        
        student_service.update(sv_id, {
            'avatar': f"{mssv}/0.jpg",
            'trang_thai_face': 1
        })
        
    # Tạo thư mục chứa ảnh
    student_dir = os.path.join(Config.DATABASE_DIR, mssv)
    os.makedirs(student_dir, exist_ok=True)
    
    saved_count = 0
    for idx, b64 in enumerate(images):
        try:
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            img_data = base64.b64decode(b64.strip())
            with open(os.path.join(student_dir, f"{idx}.jpg"), 'wb') as f:
                f.write(img_data)
            saved_count += 1
        except Exception:
            pass
            
    return jsonify({
        "success": True, 
        "message": f"Đã đăng ký tài khoản và lưu thành công {saved_count} ảnh khuôn mặt.",
        "data": {"mssv": mssv, "images_saved": saved_count}
    }), 200

@api_mobile_bp.route('/classes', methods=['GET'])
def get_classes():
    """
    Lấy danh sách lớp học cho màn hình đăng ký
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        from services import class_service
        classes = class_service.get_all(active_only=True)
        # Chỉ lấy id, ma_lop, ten_lop
        res_data = [{"id": c["id"], "ma_lop": c["ma_lop"], "ten_lop": c["ten_lop"]} for c in classes]
        return jsonify({"success": True, "data": res_data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/profile', methods=['GET'])
def get_profile():
    """
    Lấy thông tin chi tiết sinh viên/admin đang đăng nhập
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    
    user_id = payload.get('sub')
    role = payload.get('role')

    if role == 'student':
        # Join với lớp học để lấy tên lớp
        sql = """
            SELECT sv.*, lh.ten_lop, lh.ma_lop 
            FROM sinh_vien sv
            LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
            WHERE sv.id = %s
        """
        user = execute_one(sql, (user_id,))
    else:
        user = execute_one("SELECT * FROM admin WHERE id = %s", (user_id,))

    if not user:
        return jsonify({"success": False, "message": "Không tìm thấy người dùng"}), 404
        
    # Xóa password_hash trước khi trả về
    if 'password_hash' in user:
        del user['password_hash']
    
    # Format datetime
    if 'created_at' in user and user['created_at']:
        user['created_at'] = user['created_at'].strftime("%Y-%m-%d %H:%M:%S")
    if 'ngay_sinh' in user and user['ngay_sinh']:
        user['ngay_sinh'] = user['ngay_sinh'].strftime("%Y-%m-%d")

    return jsonify({"success": True, "data": user}), 200


@api_mobile_bp.route('/change-password', methods=['POST'])
def change_password():
    """
    Đổi mật khẩu cho người dùng hiện tại
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    
    data = request.get_json(silent=True) or {}
    old_pwd = data.get('old_password')
    new_pwd = data.get('new_password')
    
    if not old_pwd or not new_pwd:
        return jsonify({"success": False, "message": "Thiếu thông tin mật khẩu"}), 400
        
    user_id = payload.get('sub')
    role = payload.get('role')
    
    # Lấy hash cũ
    table = "sinh_vien" if role == "student" else "admin"
    user = execute_one(f"SELECT password_hash FROM {table} WHERE id = %s", (user_id,))
    
    if not user or not check_password_hash(user['password_hash'], old_pwd):
        return jsonify({"success": False, "message": "Mật khẩu cũ không chính xác"}), 401
    
    # Hash mật khẩu mới
    new_hash = generate_password_hash(new_pwd, method='pbkdf2:sha256')
    execute_update(f"UPDATE {table} SET password_hash = %s WHERE id = %s", (new_hash, user_id))
    
    return jsonify({"success": True, "message": "Đổi mật khẩu thành công"}), 200


@api_mobile_bp.route('/schedule', methods=['GET'])
def get_schedule():
    """
    Lấy lịch học của sinh viên
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    
    if payload.get('role') != 'student':
        return jsonify({"success": False, "message": "Chỉ sinh viên mới có lịch học"}), 403

    user_id = payload.get('sub')
    student = execute_one("SELECT lop_id FROM sinh_vien WHERE id = %s", (user_id,))
    
    if not student or not student['lop_id']:
        return jsonify({"success": True, "data": [], "message": "Sinh viên chưa được xếp lớp"}), 200
        
    # Lấy lịch học theo lớp
    sql = "SELECT * FROM lich_hoc WHERE lop_id = %s ORDER BY thu ASC, tiet_bat_dau ASC"
    schedules = execute_query(sql, (student['lop_id'],))
    
    return jsonify({"success": True, "data": schedules}), 200


@api_mobile_bp.route('/update-avatar', methods=['POST'])
def update_avatar():
    """
    Cập nhật ảnh đại diện người dùng
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    
    data = request.get_json(silent=True) or {}
    image_base64 = data.get('image') # base64 string
    
    if not image_base64:
        return jsonify({"success": False, "message": "Thiếu dữ liệu ảnh"}), 400
        
    user_id = payload.get('sub')
    role = payload.get('role')
    username = payload.get('username') # MSSV
    
    # Tạo thư mục nếu chưa có
    avatar_dir = os.path.join('static', 'uploads', 'avatars')
    os.makedirs(avatar_dir, exist_ok=True)
    
    # Dùng timestamp để tránh cache ảnh cũ
    filename = f"{username}_{int(time.time())}.jpg"
    filepath = os.path.join(avatar_dir, filename)
    db_path = f"uploads/avatars/{filename}"
    
    try:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        img_data = base64.b64decode(image_base64)
        with open(filepath, 'wb') as f:
            f.write(img_data)
            
        # Cập nhật DB
        table = "sinh_vien" if role == "student" else "admin"
        execute_update(f"UPDATE {table} SET avatar = %s WHERE id = %s", (db_path, user_id))
        
        return jsonify({"success": True, "message": "Cập nhật ảnh đại diện thành công", "avatar_url": db_path}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/pending-faces', methods=['GET'])
def get_pending_faces():
    """
    Lấy danh sách sinh viên đang chờ duyệt khuôn mặt
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error or payload.get('role') != 'admin':
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


@api_mobile_bp.route('/approve-face', methods=['POST'])
def approve_face():
    """
    Phê duyệt hoặc từ chối khuôn mặt sinh viên
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error or payload.get('role') != 'admin':
        return jsonify({"success": False, "message": "Quyền truy cập bị từ chối"}), 403

    data = request.get_json(silent=True) or {}
    sv_id = data.get('id')
    status = data.get('status') # 2: Approved, 3: Rejected
    
    if not sv_id or status not in [2, 3]:
        return jsonify({"success": False, "message": "Dữ liệu không hợp lệ"}), 400

    try:
        execute_update("UPDATE sinh_vien SET trang_thai_face = %s WHERE id = %s", (status, sv_id))
        msg = "Đã duyệt khuôn mặt" if status == 2 else "Đã từ chối khuôn mặt"
        return jsonify({"success": True, "message": msg}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/update-profile', methods=['POST'])
def update_profile():
    """
    Cập nhật thông tin chi tiết sinh viên/admin
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    
    data = request.get_json(silent=True) or {}
    user_id = payload.get('sub')
    role = payload.get('role')
    
    try:
        new_pwd = data.get('new_password')
        
        if role == 'student':
            sql = """
                UPDATE sinh_vien 
                SET email = %s, sdt = %s, que_quan = %s, dan_toc = %s
                WHERE id = %s
            """
            execute_update(sql, (data.get('email'), data.get('sdt'), data.get('que_quan'), data.get('dan_toc'), user_id))
            
            if new_pwd and new_pwd.strip():
                new_hash = generate_password_hash(new_pwd.strip(), method='pbkdf2:sha256')
                execute_update("UPDATE sinh_vien SET password_hash = %s WHERE id = %s", (new_hash, user_id))
        else:
            execute_update("UPDATE admin SET email = %s, sdt = %s WHERE id = %s", (data.get('email'), data.get('sdt'), user_id))
            
            if new_pwd and new_pwd.strip():
                new_hash = generate_password_hash(new_pwd.strip(), method='pbkdf2:sha256')
                execute_update("UPDATE admin SET password_hash = %s WHERE id = %s", (new_hash, user_id))
            
        return jsonify({"success": True, "message": "Cập nhật thông tin thành công"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/face-gallery', methods=['GET'])
def get_face_gallery():
    """
    Lấy danh sách các ảnh khuôn mặt đã đăng ký của sinh viên
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    from flask import session
    
    # Check if there's a mobile JWT
    payload, auth_error = _require_mobile_auth()
    
    # If no JWT, check if there's a web admin session
    if auth_error and not session.get('admin_id'):
        return auth_error
    
    role = payload.get('role') if payload else 'admin'
    user_id = payload.get('sub') if payload else session.get('admin_id')
    
    # Chỉ lấy MSSV nếu là sinh viên
    if role == 'student':
        user = execute_one("SELECT mssv FROM sinh_vien WHERE id = %s", (user_id,))
        if not user:
            return jsonify({"success": False, "message": "Không tìm thấy sinh viên"}), 404
        mssv = user['mssv']
    else:
        # Admin có thể xem ảnh của một sinh viên cụ thể qua query param
        mssv = request.args.get('mssv')
        if not mssv:
            return jsonify({"success": False, "message": "Thiếu MSSV"}), 400

    student_dir = os.path.join(Config.DATABASE_DIR, mssv)
    if not os.path.exists(student_dir):
        return jsonify({"success": True, "data": []}), 200
        
    try:
        # Lấy danh sách tệp .jpg hoặc .png
        images = [f for f in os.listdir(student_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        # Tạo đường dẫn URL
        image_urls = [f"{mssv}/{img}" for img in images]
        
        return jsonify({"success": True, "data": image_urls}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==============================================================================
# OFFLINE-FIRST: API ĐỒNG BỘ (SYNC) CHO MOBILE APP
# ==============================================================================

@api_mobile_bp.route('/sync/students', methods=['GET'])
def pull_students():
    """
    Đồng bộ (Pull) dữ liệu sinh viên từ Server xuống App.
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    _, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    last_sync_time_str = request.args.get('last_sync_time', '1970-01-01 00:00:00')
    try:
        last_sync_time = datetime.strptime(last_sync_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({"success": False, "message": "Sai định dạng thời gian"}), 400

    try:
        # Lấy sinh viên có sự thay đổi
        sql = """
            SELECT sv.id, sv.mssv, sv.ho_ten, sv.face_vector, sv.updated_at, sv.trang_thai
            FROM sinh_vien sv
            WHERE sv.updated_at >= %s
        """
        students = execute_query(sql, (last_sync_time,))
        
        import json
        for sv in students:
            if 'updated_at' in sv and sv['updated_at']:
                sv['updated_at'] = sv['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            if sv.get('face_vector'):
                try:
                    sv['face_vector'] = json.loads(sv['face_vector'])
                except:
                    sv['face_vector'] = None

        return jsonify({
            "success": True,
            "data": students,
            "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sync/attendance', methods=['POST'])
def push_attendance():
    """
    Đồng bộ (Push) dữ liệu điểm danh Offline từ App lên Server.
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    _, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    logs = data.get('logs', [])
    
    if not logs:
        return jsonify({"success": False, "message": "Không có dữ liệu điểm danh"}), 400

    synced_uuids = []
    errors = []

    for log in logs:
        local_uuid = log.get('local_uuid')
        mssv = log.get('mssv')
        check_time = log.get('check_time')
        confidence = float(log.get('confidence') or 0.0)

        if not local_uuid or not mssv or not check_time:
            errors.append({"local_uuid": local_uuid, "error": "Thiếu dữ liệu"})
            continue

        try:
            # 1. Kiểm tra chống trùng lặp (Idempotency) - Sử dụng ghi_chu để lưu local_uuid
            note_marker = f"OFFLINE_UUID:{local_uuid}"
            
            exist = execute_one("SELECT id FROM diem_danh WHERE ghi_chu LIKE %s", (f"%{note_marker}%",))
            if exist:
                synced_uuids.append(local_uuid)
                continue
                
            # Lấy thông tin sv
            sv = execute_one("SELECT id, lop_id FROM sinh_vien WHERE mssv = %s", (mssv,))
            if not sv:
                errors.append({"local_uuid": local_uuid, "error": "Sinh viên không tồn tại"})
                continue
                
            # 2. Lưu vào DB
            sql = """
                INSERT INTO diem_danh (sinh_vien_id, lop_id, thoi_gian, trang_thai, do_chinh_xac, ghi_chu)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            execute_update(sql, (sv['id'], sv['lop_id'], check_time, "Co mat", confidence, note_marker))
            synced_uuids.append(local_uuid)
            
        except Exception as e:
            errors.append({"local_uuid": local_uuid, "error": str(e)})

    return jsonify({
        "success": True,
        "synced_local_uuids": synced_uuids,
        "errors": errors
    }), 200


@api_mobile_bp.route('/sync/sessions', methods=['GET'])
def sync_sessions():
    """
    Đồng bộ (Pull) phiên điểm danh đang mở về App.
    Endpoint này nhẹ hơn /sessions/active - chỉ trả dữ liệu cần thiết cho offline.
    ---
    tags:
      - Mobile App API - Sync
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    try:
        # Auto-close expired sessions
        execute_update(
            "UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = NOW() WHERE trang_thai = 1 AND het_han IS NOT NULL AND het_han < NOW()"
        )

        role = payload.get('role', 'admin')
        user_id = payload.get('sub')

        if role == 'student':
            student = execute_one("SELECT lop_id, mssv FROM sinh_vien WHERE id = %s", (user_id,))
            student_mssv = student['mssv'] if student else ''

            sql = """
                SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.het_han, p.trang_thai,
                       l.ma_lop, l.ten_lop, l.giao_vien,
                       (SELECT COUNT(*) FROM diem_danh d 
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND d.trang_thai = 'Co mat') as so_da_diem_danh,
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
                SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.het_han, p.trang_thai,
                       l.ma_lop, l.ten_lop, l.giao_vien,
                       (SELECT COUNT(DISTINCT d.sinh_vien_id) FROM diem_danh d 
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND d.trang_thai = 'Co mat') as so_da_diem_danh,
                       (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = p.lop_id AND sv.trang_thai = 1) as tong_sv
                FROM phien_diem_danh p
                JOIN lop_hoc l ON p.lop_id = l.id
                WHERE p.trang_thai = 1
                ORDER BY p.bat_dau DESC
            """
            sessions = execute_query(sql)

        for s in sessions:
            if s.get('bat_dau') and hasattr(s['bat_dau'], 'strftime'):
                s['bat_dau'] = s['bat_dau'].strftime('%Y-%m-%d %H:%M:%S')
            if s.get('het_han') and hasattr(s['het_han'], 'strftime'):
                s['het_han'] = s['het_han'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            "success": True,
            "data": sessions,
            "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sync/schedule', methods=['GET'])
def sync_schedule():
    """
    Đồng bộ (Pull) lịch học về App cho sinh viên.
    ---
    tags:
      - Mobile App API - Sync
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    if payload.get('role') != 'student':
        return jsonify({"success": True, "data": [], "message": "Chỉ sinh viên mới có lịch học"}), 200

    user_id = payload.get('sub')
    student = execute_one("SELECT lop_id FROM sinh_vien WHERE id = %s", (user_id,))

    if not student or not student['lop_id']:
        return jsonify({"success": True, "data": []}), 200

    try:
        sql = "SELECT * FROM lich_hoc WHERE lop_id = %s ORDER BY thu ASC, tiet_bat_dau ASC"
        schedules = execute_query(sql, (student['lop_id'],))
        return jsonify({
            "success": True,
            "data": schedules,
            "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sync/notifications', methods=['GET'])
def sync_notifications():
    """
    Đồng bộ (Pull) thông báo về App.
    ---
    tags:
      - Mobile App API - Sync
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    user_id = payload.get('sub')
    role = payload.get('role')

    try:
        if role == 'student':
            sql = """
                SELECT id, tieu_de, noi_dung, da_doc, created_at 
                FROM thong_bao 
                WHERE sinh_vien_id = %s 
                ORDER BY created_at DESC 
                LIMIT 50
            """
            notifications = execute_query(sql, (user_id,))
        else:
            # Admin: lấy thông báo hệ thống hoặc tất cả
            sql = """
                SELECT id, tieu_de, noi_dung, da_doc, created_at 
                FROM thong_bao 
                ORDER BY created_at DESC 
                LIMIT 50
            """
            notifications = execute_query(sql)

        for n in notifications:
            if n.get('created_at') and hasattr(n['created_at'], 'strftime'):
                n['created_at'] = n['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            "success": True,
            "data": notifications,
            "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Helper: Tính khoảng cách giữa 2 điểm GPS (mét)
def get_distance_meters(lat1, lon1, lat2, lon2):
    import math
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0
    R = 6371000  # Bán kính Trái đất tính bằng mét
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ==============================================================================
# PHIÊN ĐIỂM DANH (ATTENDANCE SESSIONS) - Admin tạo, Sinh viên tham gia
# ==============================================================================

@api_mobile_bp.route('/sessions/create', methods=['POST'])
def create_session():
    """
    Admin tạo phiên điểm danh cho một lớp. Sinh viên sẽ thấy phiên này trên mobile.
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get('role') == 'student':
        return jsonify({"success": False, "message": "Chỉ Admin mới được tạo phiên điểm danh"}), 403

    data = request.get_json(silent=True) or {}
    lop_id = data.get('lop_id')
    mo_ta = data.get('mo_ta', '')
    duration_minutes = int(data.get('duration_minutes') or 90)  # Mặc định 90 phút

    if not lop_id:
        return jsonify({"success": False, "message": "Thiếu lop_id"}), 400

    # Kiểm tra lớp tồn tại
    lop = execute_one("SELECT id, ma_lop, ten_lop FROM lop_hoc WHERE id = %s AND trang_thai = 1", (lop_id,))
    if not lop:
        return jsonify({"success": False, "message": "Lớp không tồn tại hoặc đã vô hiệu hóa"}), 404

    # Kiểm tra xem lớp này đã có phiên đang mở chưa
    existing = execute_one(
        "SELECT id FROM phien_diem_danh WHERE lop_id = %s AND trang_thai = 1",
        (lop_id,)
    )
    if existing:
        return jsonify({"success": False, "message": f"Lớp {lop['ma_lop']} đã có phiên điểm danh đang mở (ID: {existing['id']})"}), 409

    # Tạo phiên mới
    het_han = datetime.now() + timedelta(minutes=duration_minutes)
    admin_id = payload.get('sub')
    vi_do = data.get('vi_do')
    kinh_do = data.get('kinh_do')
    
    new_id = execute_update(
        """INSERT INTO phien_diem_danh (lop_id, admin_id, trang_thai, mo_ta, bat_dau, het_han, vi_do, kinh_do)
           VALUES (%s, %s, 1, %s, NOW(), %s, %s, %s)""",
        (lop_id, admin_id, mo_ta, het_han.strftime('%Y-%m-%d %H:%M:%S'), vi_do, kinh_do)
    )

    # === THÔNG BÁO CHO SINH VIÊN ===
    import threading
    def _notify_students():
        try:
            # Lấy tất cả SV trong lớp
            students = execute_query(
                "SELECT id, fcm_token FROM sinh_vien WHERE lop_id = %s AND trang_thai = 1",
                (lop_id,)
            )

            title = f"📢 Điểm danh: {lop['ma_lop']}"
            body = f"Phiên điểm danh lớp {lop['ten_lop']} đã mở! Thời hạn: {duration_minutes} phút."

            for sv in students:
                # 1. Lưu thông báo trong app
                execute_update(
                    "INSERT INTO thong_bao (sinh_vien_id, tieu_de, noi_dung) VALUES (%s, %s, %s)",
                    (sv['id'], title, body)
                )

                # 2. Gửi Push Notification qua FCM
                if sv.get('fcm_token'):
                    try:
                        from services.fcm_service import send_push_notification
                        send_push_notification(
                            sv['fcm_token'], title, body,
                            data={'type': 'session_opened', 'session_id': str(new_id), 'lop_id': str(lop_id)}
                        )
                    except Exception:
                        pass

            print(f"[SESSION] Đã gửi thông báo cho {len(students)} sinh viên lớp {lop['ma_lop']}")
        except Exception as e:
            print(f"[SESSION] Lỗi gửi thông báo: {e}")

    threading.Thread(target=_notify_students, daemon=True).start()

    return jsonify({
        "success": True,
        "message": f"Đã mở phiên điểm danh cho lớp {lop['ma_lop']}",
        "data": {
            "session_id": new_id,
            "lop_id": lop_id,
            "ma_lop": lop['ma_lop'],
            "ten_lop": lop['ten_lop'],
            "het_han": het_han.strftime('%Y-%m-%d %H:%M:%S'),
            "duration_minutes": duration_minutes
        }
    }), 200


@api_mobile_bp.route('/sessions/active', methods=['GET'])
def get_active_sessions():
    """
    Lấy danh sách các phiên điểm danh đang mở.
    - Admin: xem tất cả phiên đang mở.
    - Sinh viên: chỉ xem phiên của lớp mình.
    
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    role = payload.get('role', 'admin')
    user_id = payload.get('sub')

    try:
        # Auto-close các phiên đã hết hạn
        execute_update(
            "UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = NOW() WHERE trang_thai = 1 AND het_han IS NOT NULL AND het_han < NOW()"
        )

        if role == 'student':
            # Sinh viên: Xem TẤT CẢ phiên đang mở (để có thể điểm danh bất kỳ lớp nào admin mở)
            student = execute_one("SELECT lop_id, mssv FROM sinh_vien WHERE id = %s", (user_id,))
            student_mssv = student['mssv'] if student else ''

            sql = """
                SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.het_han,
                       l.ma_lop, l.ten_lop, l.giao_vien,
                       (SELECT COUNT(*) FROM diem_danh d 
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND d.trang_thai = 'Co mat') as so_da_diem_danh,
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
            # Admin: xem tất cả
            sql = """
                SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.het_han,
                       l.ma_lop, l.ten_lop, l.giao_vien,
                       (SELECT COUNT(DISTINCT d.sinh_vien_id) FROM diem_danh d 
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND d.trang_thai = 'Co mat') as so_da_diem_danh,
                       (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = p.lop_id AND sv.trang_thai = 1) as tong_sv
                FROM phien_diem_danh p
                JOIN lop_hoc l ON p.lop_id = l.id
                WHERE p.trang_thai = 1
                ORDER BY p.bat_dau DESC
            """
            sessions = execute_query(sql)

        # Format datetime
        for s in sessions:
            if s.get('bat_dau'):
                s['bat_dau'] = s['bat_dau'].strftime('%Y-%m-%d %H:%M:%S')
            if s.get('het_han'):
                s['het_han'] = s['het_han'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({"success": True, "data": sessions}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sessions/<int:session_id>/stop', methods=['POST'])
def stop_session_api(session_id):
    """Admin đóng phiên điểm danh."""
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get('role') == 'student':
        return jsonify({"success": False, "message": "Chỉ Admin mới được đóng phiên"}), 403

    session = execute_one("SELECT * FROM phien_diem_danh WHERE id = %s", (session_id,))
    if not session:
        return jsonify({"success": False, "message": "Phiên không tồn tại"}), 404
    if session['trang_thai'] == 0:
        return jsonify({"success": False, "message": "Phiên đã đóng trước đó"}), 409

    execute_update(
        "UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = NOW() WHERE id = %s",
        (session_id,)
    )

    # --- TÍNH TOÁN THỐNG KÊ ĐỂ GỬI TELEGRAM ---
    try:
        lop_id = session['lop_id']
        lop = execute_one("SELECT ten_lop, ma_lop FROM lop_hoc WHERE id = %s", (lop_id,))
        
        # Lấy số lượng đi học
        present_sql = """
            SELECT COUNT(DISTINCT sinh_vien_id) as count 
            FROM diem_danh 
            WHERE lop_id = %s AND thoi_gian >= %s AND thoi_gian <= NOW()
        """
        present_count = execute_one(present_sql, (lop_id, session['bat_dau']))['count']
        
        # Lấy tổng sĩ số
        total_sv = execute_one("SELECT COUNT(*) as count FROM sinh_vien WHERE lop_id = %s AND trang_thai = 1", (lop_id,))['count']
        absent_count = total_sv - present_count
        
        # Lấy danh sách SV vắng
        absent_sv_sql = """
            SELECT id, ho_ten FROM sinh_vien 
            WHERE lop_id = %s AND trang_thai = 1 
            AND id NOT IN (
                SELECT sinh_vien_id FROM diem_danh 
                WHERE lop_id = %s AND thoi_gian >= %s AND thoi_gian <= NOW()
            )
        """
        absent_list = execute_query(absent_sv_sql, (lop_id, lop_id, session['bat_dau']))
        absent_names = ", ".join([sv['ho_ten'] for sv in absent_list]) if absent_list else "Không có"

        # Gửi thông báo vào App cho từng sinh viên vắng
        for sv_absent in absent_list:
            execute_update(
                "INSERT INTO thong_bao (sinh_vien_id, tieu_de, noi_dung) VALUES (%s, %s, %s)",
                (sv_absent['id'], "Cảnh báo vắng học", f"Bạn đã vắng mặt trong buổi học lớp {lop['ten_lop']} vào lúc {session['bat_dau'].strftime('%H:%M')}.")
            )

        # Gửi Telegram cho giảng viên
        msg = (
            f"🔔 <b>THÔNG BÁO KẾT THÚC ĐIỂM DANH</b>\n"
            f"--------------------------------\n"
            f"🏫 <b>Lớp:</b> {lop['ten_lop']} ({lop['ma_lop']})\n"
            f"⏰ <b>Bắt đầu:</b> {session['bat_dau'].strftime('%H:%M:%S')}\n"
            f"✅ <b>Có mặt:</b> {present_count}/{total_sv}\n"
            f"❌ <b>Vắng:</b> {absent_count}\n"
            f"📝 <b>Danh sách vắng:</b> {absent_names}\n"
        )
        send_telegram_message(msg)
    except Exception as e:
        print(f"Lỗi gửi thông báo Telegram: {e}")

    return jsonify({"success": True, "message": "Đã đóng phiên điểm danh và gửi báo cáo Telegram"}), 200


@api_mobile_bp.route('/sessions/<int:session_id>/details', methods=['GET'])
def get_session_details(session_id):
    """
    /sessions/<int:session_id>/details
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get('role') == 'student':
            return jsonify({"success": False, "message": "Chỉ Admin mới được xem chi tiết"}), 403

        session = execute_one(
            "SELECT p.*, l.ten_lop, l.ma_lop FROM phien_diem_danh p JOIN lop_hoc l ON p.lop_id = l.id WHERE p.id = %s",
            (session_id,)
        )
        if not session:
            return jsonify({"success": False, "message": "Phiên không tồn tại"}), 404

        lop_id = session['lop_id']
        
        sql = """
            SELECT sv.id, sv.mssv, sv.ho_ten, sv.avatar,
                   d.thoi_gian, d.trang_thai, d.ghi_chu
            FROM sinh_vien sv
            LEFT JOIN diem_danh d ON sv.id = d.sinh_vien_id 
                  AND d.lop_id = %s 
                  AND d.thoi_gian >= %s
            WHERE sv.lop_id = %s AND sv.trang_thai = 1
            ORDER BY sv.mssv ASC
        """
        students = execute_query(sql, (lop_id, session['bat_dau'], lop_id))

        for s in students:
            if s.get('thoi_gian') and hasattr(s['thoi_gian'], 'strftime'):
                s['thoi_gian'] = s['thoi_gian'].strftime('%H:%M:%S')

        bat_dau_str = session['bat_dau'].strftime('%Y-%m-%d %H:%M:%S') if session.get('bat_dau') and hasattr(session['bat_dau'], 'strftime') else str(session.get('bat_dau'))

        return jsonify({
            "success": True, 
            "data": {
                "session": {
                    "id": session['id'],
                    "ten_lop": session['ten_lop'],
                    "ma_lop": session['ma_lop'],
                    "bat_dau": bat_dau_str,
                    "trang_thai": session['trang_thai']
                },
                "students": students
            }
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sessions/history', methods=['GET'])
def get_session_history():
    """
    Lấy lịch sử phiên điểm danh đã đóng
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get('role') == 'student':
            return jsonify({"success": False, "message": "Chỉ Admin mới được xem"}), 403

        sql = """
            SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.ket_thuc, p.het_han,
                   l.ma_lop, l.ten_lop, l.giao_vien,
                   (SELECT COUNT(*) FROM diem_danh d 
                    WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                    AND (p.ket_thuc IS NULL OR d.thoi_gian <= p.ket_thuc)
                    AND d.trang_thai = 'Co mat') as so_da_diem_danh,
                   (SELECT COUNT(*) FROM sinh_vien sv 
                    WHERE sv.lop_id = p.lop_id AND sv.trang_thai = 1) as tong_sv
            FROM phien_diem_danh p
            JOIN lop_hoc l ON p.lop_id = l.id
            WHERE p.trang_thai = 0
            ORDER BY p.bat_dau DESC
            LIMIT 100
        """
        sessions = execute_query(sql)
        
        for s in sessions:
            for key in ['bat_dau', 'ket_thuc', 'het_han']:
                if s.get(key) and hasattr(s[key], 'strftime'):
                    s[key] = s[key].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({"success": True, "data": sessions}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Xóa phiên điểm danh và dữ liệu điểm danh liên quan
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get('role') == 'student':
            return jsonify({"success": False, "message": "Chỉ Admin mới được xóa"}), 403

        session = execute_one("SELECT id, lop_id, bat_dau, ket_thuc FROM phien_diem_danh WHERE id = %s", (session_id,))
        if not session:
            return jsonify({"success": False, "message": "Phiên không tồn tại"}), 404

        # Xóa dữ liệu điểm danh thuộc phiên này (theo lop_id + khoảng thời gian)
        if session.get('ket_thuc'):
            execute_update(
                "DELETE FROM diem_danh WHERE lop_id = %s AND thoi_gian >= %s AND thoi_gian <= %s",
                (session['lop_id'], session['bat_dau'], session['ket_thuc'])
            )
        else:
            execute_update(
                "DELETE FROM diem_danh WHERE lop_id = %s AND thoi_gian >= %s",
                (session['lop_id'], session['bat_dau'])
            )
        
        # Xóa phiên
        execute_update("DELETE FROM phien_diem_danh WHERE id = %s", (session_id,))

        return jsonify({"success": True, "message": "Đã xóa phiên điểm danh"}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500



@api_mobile_bp.route('/student/checkin', methods=['POST'])
def student_self_checkin():
    """
    API đặc biệt cho sinh viên tự điểm danh bằng khuôn mặt.
    Server sẽ nhận diện khuôn mặt và xác minh đúng sinh viên đang đăng nhập.
    
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    if payload.get('role') != 'student':
        return jsonify({"success": False, "message": "API này chỉ dành cho sinh viên"}), 403

    data = request.get_json(silent=True) or {}
    session_id = data.get('session_id')
    image_base64 = data.get('image_base64')
    sv_lat = data.get('vi_do')
    sv_lng = data.get('kinh_do')

    if not session_id:
        return jsonify({"success": False, "message": "Thiếu session_id"}), 400
    if not image_base64:
        return jsonify({"success": False, "message": "Thiếu ảnh khuôn mặt"}), 400

    # Lấy thông tin SV đang đăng nhập
    student_mssv = payload.get('username')
    student_id = payload.get('sub')

    # Kiểm tra phiên
    session = execute_one(
        "SELECT * FROM phien_diem_danh WHERE id = %s AND trang_thai = 1",
        (session_id,)
    )
    if not session:
        return jsonify({"success": False, "message": "Phiên điểm danh không tồn tại hoặc đã đóng"}), 403

    if session.get('het_han') and datetime.now() > session['het_han']:
        execute_update("UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = NOW() WHERE id = %s", (session_id,))
        return jsonify({"success": False, "message": "Phiên điểm danh đã hết hạn"}), 403

    # KIỂM TRA GPS (Geofencing)
    # Chỉ kiểm tra nếu Admin đã lưu vị trí lớp học
    if session.get('vi_do') is not None and session.get('kinh_do') is not None:
        if sv_lat is None or sv_lng is None:
            return jsonify({
                "success": False, 
                "message": "Hệ thống yêu cầu quyền truy cập vị trí để xác minh bạn đang ở lớp học."
            }), 400
            
        distance = calculate_distance(sv_lat, sv_lng, session['vi_do'], session['kinh_do'])
        max_radius = 50  # Bán kính 50 mét
        
        if distance > max_radius:
            return jsonify({
                "success": False,
                "message": f"Bạn đang ở quá xa lớp học ({int(distance)}m). Vui lòng đến lớp để điểm danh."
            }), 403

    lop_id = session['lop_id']

    # Kiểm tra SV tồn tại
    sv = execute_one("SELECT id, lop_id, ho_ten FROM sinh_vien WHERE mssv = %s", (student_mssv,))
    if not sv:
        return jsonify({"success": False, "message": "Không tìm thấy thông tin sinh viên"}), 404

    # Gửi ảnh lên server nhận diện khuôn mặt
    from routes.public import _do_recognize
    recognize_result = _do_recognize(image_base64)

    if not recognize_result or not recognize_result.get('success'):
        return jsonify({
            "success": False,
            "message": recognize_result.get('msg', 'Không nhận diện được khuôn mặt') if recognize_result else 'Lỗi nhận diện'
        }), 400

    # Xác minh khuôn mặt khớp với sinh viên đang đăng nhập
    recognized_mssv = recognize_result.get('student', {}).get('mssv', '')
    if recognized_mssv != student_mssv:
        return jsonify({
            "success": False,
            "message": "Khuôn mặt không khớp với tài khoản đang đăng nhập! Vui lòng tự quét khuôn mặt của chính bạn."
        }), 403

    # Lưu ảnh bằng chứng
    evidence_path = None
    try:
        evidence_path = _save_evidence_image(image_base64, student_mssv)
    except Exception:
        pass

    # Ghi nhận điểm danh
    confidence = float(recognize_result.get('student', {}).get('do_chinh_xac', 0.0))
    log_result = attendance_service.log(
        mssv=student_mssv,
        lop_id=lop_id,
        do_chinh_xac=confidence,
        camera_id=0,
        trang_thai='Co mat',
        session_start_time=session['bat_dau']
    )

    if not log_result:
        return jsonify({
            "success": False,
            "message": "Bạn đã điểm danh rồi hoặc đang trong thời gian chờ"
        }), 409

    if evidence_path:
        execute_update(
            "UPDATE diem_danh SET ghi_chu = %s WHERE sinh_vien_id = %s AND lop_id = %s AND DATE(thoi_gian) = CURDATE() ORDER BY id DESC LIMIT 1",
            (f"EVIDENCE:{evidence_path}", sv['id'], lop_id),
        )

    # Thêm thông báo cá nhân cho sinh viên
    try:
        lop_info = execute_one("SELECT ten_lop FROM lop_hoc WHERE id = %s", (lop_id,))
        ten_lop = lop_info['ten_lop'] if lop_info else f"Lớp ID: {lop_id}"
        execute_update(
            "INSERT INTO thong_bao (sinh_vien_id, tieu_de, noi_dung) VALUES (%s, %s, %s)",
            (sv['id'], "Điểm danh thành công", f"Bạn đã điểm danh thành công lớp {ten_lop} vào lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}.")
        )
    except Exception as e:
        print(f"Lỗi tạo thông báo: {e}")

    return jsonify({
        "success": True,
        "message": f"Điểm danh thành công! Xin chào {sv['ho_ten']}",
        "data": {
            "mssv": student_mssv,
            "ho_ten": sv['ho_ten'],
            "action": log_result.get('action'),
            "do_chinh_xac": confidence,
            "evidence_path": evidence_path
        }
    }), 200


# ==============================================================================
# THỐNG KÊ & BIỂU ĐỒ (ANALYTICS)
# ==============================================================================

@api_mobile_bp.route('/stats/classes', methods=['GET'])
def get_class_stats():
    """
    Lấy tỉ lệ đi học của từng lớp
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        sql = """
            SELECT l.id, l.ma_lop, l.ten_lop,
                   (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = l.id AND sv.trang_thai = 1) as tong_sv,
                   (SELECT COUNT(DISTINCT d.sinh_vien_id) FROM diem_danh d 
                    WHERE d.lop_id = l.id AND DATE(d.thoi_gian) = CURDATE()) as so_co_mat_hom_nay
            FROM lop_hoc l
            WHERE l.trang_thai = 1
        """
        results = execute_query(sql)
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/stats/absent-risk', methods=['GET'])
def get_absent_risk():
    """
    Danh sách SV vắng nhiều (ví dụ > 2 lần)
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        # Ở đây ta giả định nếu SV không có trong bảng diem_danh của một phiên lớp họ thì là vắng.
        # Để đơn giản, ta lấy SV có tổng số lần 'Co mat' thấp nhất so với số phiên đã mở của lớp đó.
        sql = """
            SELECT sv.mssv, sv.ho_ten, l.ma_lop,
                   (SELECT COUNT(*) FROM phien_diem_danh p WHERE p.lop_id = sv.lop_id AND p.trang_thai = 0) as tong_buoi_hoc,
                   (SELECT COUNT(*) FROM diem_danh d WHERE d.sinh_vien_id = sv.id AND d.trang_thai = 'Co mat') as so_buoi_di
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

@api_mobile_bp.route('/stats/daily-trend', methods=['GET'])
def get_daily_trend():
    """
    Xu hướng điểm danh 7 ngày gần nhất
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        sql = """
            SELECT DATE(thoi_gian) as ngay, COUNT(*) as so_luong
            FROM diem_danh
            WHERE thoi_gian >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY DATE(thoi_gian)
            ORDER BY ngay ASC
        """
        results = execute_query(sql)
        # Convert date objects to strings
        for r in results:
            if hasattr(r['ngay'], 'strftime'):
                r['ngay'] = r['ngay'].strftime('%d/%m')
                
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ==============================================================================
# THÔNG BÁO (NOTIFICATIONS)
# ==============================================================================

@api_mobile_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """
    Lấy danh sách thông báo của sinh viên
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        # Chỉ sinh viên mới có thông báo cá nhân, Admin sẽ không thấy thông báo của sinh viên có cùng ID
        if payload.get('role') != 'student':
            return jsonify({"success": True, "data": []}), 200

        user_id = payload.get('sub')
        sql = "SELECT * FROM thong_bao WHERE sinh_vien_id = %s ORDER BY created_at DESC LIMIT 50"
        results = execute_query(sql, (user_id,))
        
        for r in results:
            if hasattr(r['created_at'], 'strftime'):
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
def mark_notification_read(notif_id):
    """
    Đánh dấu thông báo đã đọc
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        execute_update("UPDATE thong_bao SET da_doc = 1 WHERE id = %s", (notif_id,))
        return jsonify({"success": True, "message": "Đã đọc"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    """
    Đánh dấu tất cả thông báo đã đọc
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        user_id = payload.get('sub')
        execute_update("UPDATE thong_bao SET da_doc = 1 WHERE sinh_vien_id = %s", (user_id,))
        return jsonify({"success": True, "message": "Đã đọc tất cả"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ================================================================
# AI CHATBOT (Hỏi đáp AI trên Mobile)
# ================================================================

@api_mobile_bp.route('/chatbot/ask', methods=['POST'])
def mobile_chatbot_ask():
    """
    Gửi câu hỏi cho AI Chatbot từ Mobile App
    ---
    tags:
      - Mobile App API
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            question:
              type: string
              example: "Hệ thống điểm danh hoạt động như thế nào?"
    responses:
      200:
        description: Trả lời thành công
      400:
        description: Câu hỏi trống hoặc quá dài
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()

    if not question:
        return jsonify({"success": False, "message": "Câu hỏi không được để trống"}), 400

    if len(question) > 2000:
        return jsonify({"success": False, "message": "Câu hỏi quá dài (tối đa 2000 ký tự)"}), 400

    # Session ID riêng cho mỗi user mobile
    user_id = payload.get('sub', 'unknown')
    session_id = f"mobile_{user_id}"

    try:
        from services.ai_chatbot import get_chatbot
        chatbot = get_chatbot()
        result = chatbot.chat(question, session_id)

        return jsonify({
            "success": True,
            "data": {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "duration_ms": result.get("duration_ms", 0),
                "backend": result.get("backend", "unknown"),
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi AI Chatbot: {str(e)}"}), 500


@api_mobile_bp.route('/chatbot/suggestions', methods=['GET'])
def mobile_chatbot_suggestions():
    """
    Lấy danh sách câu hỏi gợi ý cho chatbot
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    try:
        from services.ai_chatbot import get_chatbot
        chatbot = get_chatbot()
        suggestions = chatbot.get_suggested_questions()
        return jsonify({"success": True, "data": suggestions}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/chatbot/clear', methods=['POST'])
def mobile_chatbot_clear():
    """
    Xóa lịch sử chat AI trên mobile
    ---
    tags:
      - Mobile App API
    responses:
      200:
        description: Thành công
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    user_id = payload.get('sub', 'unknown')
    session_id = f"mobile_{user_id}"

    try:
        from services.ai_chatbot import get_chatbot
        chatbot = get_chatbot()
        chatbot.clear_history(session_id)
        return jsonify({"success": True, "message": "Đã xóa lịch sử chat"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ==============================================================================
# QUẢN LÝ SINH VIÊN (ADMIN ONLY)
# ==============================================================================

@api_mobile_bp.route('/admin/students', methods=['GET'])
def mobile_admin_get_students():
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        if payload.get('role') != 'admin':
            return jsonify({"success": False, "message": "Access Denied"}), 403

        query = request.args.get('q', '').strip()
        sql = """
            SELECT sv.id, sv.ho_ten, sv.mssv, sv.trang_thai, sv.sdt, sv.email, l.ma_lop
            FROM sinh_vien sv
            LEFT JOIN lop_hoc l ON sv.lop_id = l.id
        """
        params = []
        if query:
            sql += " WHERE sv.ho_ten LIKE %s OR sv.mssv LIKE %s"
            params = [f"%{query}%", f"%{query}%"]
        sql += " ORDER BY sv.ho_ten ASC LIMIT 100"

        students = execute_query(sql, tuple(params))
        return jsonify({"success": True, "data": students}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/admin/students/<int:student_id>', methods=['PUT'])
def mobile_admin_update_student(student_id):
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        if payload.get('role') != 'admin':
            return jsonify({"success": False, "message": "Access Denied"}), 403

        data = request.get_json() or {}
        ho_ten = data.get('ho_ten', '').strip()
        mssv = data.get('mssv', '').strip()
        ma_lop = data.get('ma_lop', '').strip()
        email = data.get('email', '').strip()
        sdt = data.get('sdt', '').strip()

        if not ho_ten or not mssv:
            return jsonify({"success": False, "message": "Họ tên và MSSV không được để trống"}), 400

        exist = execute_query("SELECT id FROM sinh_vien WHERE mssv = %s AND id != %s", (mssv, student_id))
        if exist:
            return jsonify({"success": False, "message": "MSSV đã tồn tại"}), 400

        lop_id = None
        if ma_lop:
            lop = execute_query("SELECT id FROM lop_hoc WHERE ma_lop = %s", (ma_lop,))
            if lop: lop_id = lop[0]['id']

        execute_update("""
            UPDATE sinh_vien 
            SET ho_ten=%s, mssv=%s, lop_id=%s, email=%s, sdt=%s 
            WHERE id=%s
        """, (ho_ten, mssv, lop_id, email, sdt, student_id))

        return jsonify({"success": True, "message": "Cập nhật thành công"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/admin/students/<int:student_id>', methods=['DELETE'])
def mobile_admin_delete_student(student_id):
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        if payload.get('role') != 'admin':
            return jsonify({"success": False, "message": "Access Denied"}), 403

        execute_update("DELETE FROM user_encodings WHERE mssv = (SELECT mssv FROM sinh_vien WHERE id = %s)", (student_id,))
        execute_update("DELETE FROM sinh_vien WHERE id = %s", (student_id,))

        return jsonify({"success": True, "message": "Đã xóa sinh viên"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/admin/students/<int:student_id>/reset-face', methods=['POST'])
def mobile_admin_reset_face(student_id):
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        if payload.get('role') != 'admin':
            return jsonify({"success": False, "message": "Access Denied"}), 403

        sv = execute_query("SELECT mssv FROM sinh_vien WHERE id=%s", (student_id,))
        if not sv:
            return jsonify({"success": False, "message": "Không tìm thấy sinh viên"}), 404
        
        mssv = sv[0]['mssv']
        execute_update("DELETE FROM user_encodings WHERE mssv = %s", (mssv,))
        execute_update("UPDATE sinh_vien SET trang_thai_khuon_mat=0 WHERE id=%s", (student_id,))

        import os
        import shutil
        from flask import current_app
        dataset_path = os.path.join(current_app.root_path, 'dataset', mssv)
        if os.path.exists(dataset_path):
            shutil.rmtree(dataset_path)

        return jsonify({"success": True, "message": "Đã xóa dữ liệu khuôn mặt"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
