"""
API Dành cho Mobile App (JSON Responses)
"""

import os
import uuid
import base64
from datetime import datetime, timedelta

import jwt
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from db.connection import execute_one, execute_query, execute_update
from config import Config
from services import attendance_service

# Blueprint sẽ được register trong routes/__init__.py
api_mobile_bp = Blueprint('api_mobile', __name__, url_prefix='/api/mobile')


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
    """API Đăng nhập cho ứng dụng di động"""
    data = request.get_json(silent=True) or {}
    if 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "message": "Thiếu dữ liệu đăng nhập"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
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


@api_mobile_bp.route('/checkin', methods=['POST'])
def mobile_checkin():
    """
    Check-in từ mobile.
    Payload:
    {
      "mssv": "20012001",
      "lop_id": 1,
      "do_chinh_xac": 0.92,
      "camera_id": 0,
      "trang_thai": "Co mat",
      "image_base64": "data:image/jpeg;base64,..."
    }
    """
    _, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form.to_dict()
    mssv = (data.get("mssv") or "").strip()
    lop_id = data.get("lop_id")
    do_chinh_xac = float(data.get("do_chinh_xac") or 0.0)
    camera_id = int(data.get("camera_id") or 0)
    trang_thai = (data.get("trang_thai") or "Co mat").strip()
    image_base64 = data.get("image_base64")
    session_start = data.get("session_start")

    in_window, window_error = _is_within_checkin_window(session_start)
    if not in_window:
        return jsonify({"success": False, "message": window_error}), 403

    if not mssv:
        return jsonify({"success": False, "message": "Thiếu MSSV"}), 400
    if lop_id is None:
        return jsonify({"success": False, "message": "Thiếu lop_id"}), 400

    sv = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,))
    if not sv:
        return jsonify({"success": False, "message": "Không tìm thấy sinh viên"}), 404

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
            "message": "Check-in bị bỏ qua (cooldown hoặc chưa đủ điều kiện checkout)",
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
    """Checkout riêng cho mobile app."""
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
    """Lấy thống kê điểm danh trong ngày cho màn hình chính"""
    _, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    today_str = datetime.now().strftime('%Y-%m-%d')
    try:
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
    """Lấy danh sách điểm danh gần đây"""
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    limit = request.args.get('limit', 20, type=int)
    mssv_query = request.args.get('mssv')
    
    # Nếu là sinh viên, CHỈ cho phép xem lịch sử của chính mình
    if payload and payload.get('role') == 'student':
        mssv_query = payload.get('username')
        
    try:
        sql = """
            SELECT dd.thoi_gian, dd.gio_ra, dd.trang_thai, dd.do_chinh_xac, dd.ghi_chu,
                   sv.ho_ten, sv.mssv, sv.avatar, l.ma_lop 
            FROM diem_danh dd
            JOIN sinh_vien sv ON dd.sinh_vien_id = sv.id
            LEFT JOIN lop_hoc l ON dd.lop_id = l.id
            WHERE (%s IS NULL OR sv.mssv = %s)
            ORDER BY dd.thoi_gian DESC
            LIMIT %s
        """
        records = execute_query(sql, (mssv_query, mssv_query, limit))
        
        # Chuyển đổi datetime sang chuỗi để JSON Serializable
        for row in records:
            if 'thoi_gian' in row and row['thoi_gian']:
                row['thoi_gian'] = row['thoi_gian'].strftime("%Y-%m-%d %H:%M:%S")
            if 'gio_ra' in row and row['gio_ra']:
                row['gio_ra'] = row['gio_ra'].strftime("%Y-%m-%d %H:%M:%S")
            note = row.get('ghi_chu') or ""
            if note.startswith("EVIDENCE:"):
                row['evidence_path'] = note.replace("EVIDENCE:", "", 1)
            else:
                row['evidence_path'] = None
                
        return jsonify({"success": True, "data": records}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_mobile_bp.route('/register_face', methods=['POST'])
def mobile_register_face():
    """API để Mobile App đăng ký khuôn mặt học sinh trực tiếp"""
    _, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

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
    
    # Kiểm tra xem sinh viên đã tồn tại chưa bằng query trực tiếp (đề phòng)
    sv = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,))
    if sv:
        return jsonify({"success": False, "message": "MSSV đã tồn tại trong hệ thống"}), 409
        
    student_data = {
        'mssv': mssv,
        'ho_ten': ho_ten,
        'lop_id': int(lop_id),
        'avatar': f"{mssv}/0.jpg" if images else None
    }
    
    try:
        student_id = student_service.create(student_data)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi tạo dữ liệu sinh viên: {str(e)}'}), 500
        
    if student_id is None or student_id < 0:
        return jsonify({'success': False, 'message': 'Không thể thêm dữ liệu sinh viên vào DB. Kiểm tra lại bảng sinh_vien.'}), 500
        
    # Tạo thư mục
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
    """Lấy danh sách lớp học cho màn hình đăng ký"""
    try:
        from services import class_service
        classes = class_service.get_all(active_only=True)
        # Chỉ lấy id, ma_lop, ten_lop
        res_data = [{"id": c["id"], "ma_lop": c["ma_lop"], "ten_lop": c["ten_lop"]} for c in classes]
        return jsonify({"success": True, "data": res_data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
