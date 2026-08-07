"""
Mobile Auth & Profile API routes.
"""

import os
import time
import base64
from flask import request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from db.connection import execute_one, execute_update
from config import Config
from . import api_mobile_bp
from .helpers import _make_token, _require_mobile_auth, limiter


@api_mobile_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def mobile_login():
    """
    API Đăng nhập cho ứng dụng di động
    """
    data = request.get_json(silent=True) or {}
    if "username" not in data or "password" not in data:
        return jsonify({"success": False, "message": "Thiếu dữ liệu đăng nhập"}), 400

    username = data.get("username")
    password = data.get("password")
    device_id = data.get("device_id")

    # Query thử bảng admin trước tiên
    admin = execute_one("SELECT * FROM admin WHERE username = %s", (username,))
    if admin and check_password_hash(admin["password_hash"], password):
        token = _make_token(admin, is_student=False)
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Đăng nhập Admin thành công",
                    "token": token,
                    "token_type": "Bearer",
                    "expires_in_hours": Config.JWT_EXPIRE_HOURS,
                    "user": {
                        "id": admin["id"],
                        "username": admin["username"],
                        "role": admin["role"],
                        "name": admin["ho_ten"],
                    },
                }
            ),
            200,
        )

    # Tiếp theo thử bảng sinh_vien
    student = execute_one(
        "SELECT * FROM sinh_vien WHERE mssv = %s AND trang_thai = 1", (username,)
    )
    if (
        student
        and student["password_hash"]
        and check_password_hash(student["password_hash"], password)
    ):
        # === DEVICE BINDING ===
        if not device_id:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Thiếu thông tin thiết bị (Device ID). Vui lòng cập nhật App!",
                    }
                ),
                400,
            )

        current_device = student.get("device_id")
        if not current_device or current_device != device_id:
            # Tự động cập nhật thiết bị mới khi đăng nhập ở máy khác (bỏ giới hạn 1 máy)
            execute_update(
                "UPDATE sinh_vien SET device_id = %s WHERE id = %s",
                (device_id, student["id"]),
            )

        token = _make_token(student, is_student=True)
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Đăng nhập Sinh viên thành công",
                    "token": token,
                    "token_type": "Bearer",
                    "expires_in_hours": Config.JWT_EXPIRE_HOURS,
                    "user": {
                        "id": student["id"],
                        "username": student["mssv"],
                        "role": "student",
                        "name": student["ho_ten"],
                    },
                }
            ),
            200,
        )

    return jsonify({"success": False, "message": "Sai tài khoản hoặc mật khẩu"}), 401


@api_mobile_bp.route("/fcm-token", methods=["POST"])
def update_fcm_token():
    """
    Cập nhật FCM Device Token cho Mobile
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    token = data.get("fcm_token")

    if not token:
        return jsonify({"success": False, "message": "Thiếu fcm_token"}), 400

    user_id = payload.get("sub")
    role = payload.get("role")

    if role == "student":
        execute_update(
            "UPDATE sinh_vien SET fcm_token = %s WHERE id = %s", (token, user_id)
        )
    else:
        execute_update(
            "UPDATE admin SET fcm_token = %s WHERE id = %s", (token, user_id)
        )

    return jsonify({"success": True, "message": "Cập nhật FCM Token thành công"}), 200


@api_mobile_bp.route("/profile", methods=["GET"])
def get_profile():
    """
    Lấy thông tin chi tiết sinh viên/admin đang đăng nhập
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    user_id = payload.get("sub")
    role = payload.get("role")

    if role == "student":
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
    if "password_hash" in user:
        del user["password_hash"]

    # Format datetime
    if "created_at" in user and user["created_at"]:
        user["created_at"] = user["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    if "ngay_sinh" in user and user["ngay_sinh"]:
        user["ngay_sinh"] = user["ngay_sinh"].strftime("%Y-%m-%d")

    return jsonify({"success": True, "data": user}), 200


@api_mobile_bp.route("/change-password", methods=["POST"])
def change_password():
    """
    Đổi mật khẩu cho người dùng hiện tại
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    old_pwd = data.get("old_password")
    new_pwd = data.get("new_password")

    if not old_pwd or not new_pwd:
        return jsonify({"success": False, "message": "Thiếu thông tin mật khẩu"}), 400

    user_id = payload.get("sub")
    role = payload.get("role")

    # Lấy hash cũ
    table = "sinh_vien" if role == "student" else "admin"
    user = execute_one(f"SELECT password_hash FROM {table} WHERE id = %s", (user_id,))

    if not user or not check_password_hash(user["password_hash"], old_pwd):
        return (
            jsonify({"success": False, "message": "Mật khẩu cũ không chính xác"}),
            401,
        )

    # Hash mật khẩu mới
    new_hash = generate_password_hash(new_pwd, method="pbkdf2:sha256")
    execute_update(
        f"UPDATE {table} SET password_hash = %s WHERE id = %s", (new_hash, user_id)
    )

    return jsonify({"success": True, "message": "Đổi mật khẩu thành công"}), 200


@api_mobile_bp.route("/update-avatar", methods=["POST"])
def update_avatar():
    """
    Cập nhật ảnh đại diện người dùng
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    image_base64 = data.get("image")  # base64 string

    if not image_base64:
        return jsonify({"success": False, "message": "Thiếu dữ liệu ảnh"}), 400

    user_id = payload.get("sub")
    role = payload.get("role")
    username = payload.get("username")  # MSSV

    # Tạo thư mục nếu chưa có
    avatar_dir = os.path.join(Config.DATABASE_DIR, "uploads", "avatars")
    os.makedirs(avatar_dir, exist_ok=True)

    # Dùng timestamp để tránh cache ảnh cũ
    filename = f"{username}_{int(time.time())}.jpg"
    filepath = os.path.join(avatar_dir, filename)
    db_path = f"uploads/avatars/{filename}"

    try:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        img_data = base64.b64decode(image_base64)
        with open(filepath, "wb") as f:
            f.write(img_data)

        # Cập nhật DB
        table = "sinh_vien" if role == "student" else "admin"
        execute_update(
            f"UPDATE {table} SET avatar = %s WHERE id = %s", (db_path, user_id)
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Cập nhật ảnh đại diện thành công",
                    "avatar_url": db_path,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/update-profile", methods=["POST"])
def update_profile():
    """
    Cập nhật thông tin chi tiết sinh viên/admin
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    user_id = payload.get("sub")
    role = payload.get("role")

    try:
        new_pwd = data.get("new_password")

        if role == "student":
            sql = """
                UPDATE sinh_vien 
                SET email = %s, sdt = %s, que_quan = %s, dan_toc = %s
                WHERE id = %s
            """
            execute_update(
                sql,
                (
                    data.get("email"),
                    data.get("sdt"),
                    data.get("que_quan"),
                    data.get("dan_toc"),
                    user_id,
                ),
            )

            if new_pwd and new_pwd.strip():
                new_hash = generate_password_hash(
                    new_pwd.strip(), method="pbkdf2:sha256"
                )
                execute_update(
                    "UPDATE sinh_vien SET password_hash = %s WHERE id = %s",
                    (new_hash, user_id),
                )
        else:
            execute_update(
                "UPDATE admin SET email = %s, sdt = %s WHERE id = %s",
                (data.get("email"), data.get("sdt"), user_id),
            )

            if new_pwd and new_pwd.strip():
                new_hash = generate_password_hash(
                    new_pwd.strip(), method="pbkdf2:sha256"
                )
                execute_update(
                    "UPDATE admin SET password_hash = %s WHERE id = %s",
                    (new_hash, user_id),
                )

        return (
            jsonify({"success": True, "message": "Cập nhật thông tin thành công"}),
            200,
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
