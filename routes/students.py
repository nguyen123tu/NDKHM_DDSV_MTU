"""
Route Quản lý Sinh viên (CRUD)
"""

import os
import cv2
import numpy as np
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from . import students_bp
from utils.helpers import allowed_image
from services import student_service, class_service
from db.connection import execute_query, execute_update
from utils.decorators import login_required, admin_required
from config import Config
from core.image_validator import save_validated_image

import base64


@students_bp.route("/")
@login_required
def list_students():
    """
    /
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    lop_id = request.args.get("lop_id", type=int)

    data = student_service.get_all(lop_id=lop_id, search=search, page=page)
    classes = class_service.get_all()

    return render_template(
        "students/list.html",
        students=data["items"],
        pagination=data,
        classes=classes,
        current_search=search,
        current_lop_id=lop_id,
    )


@students_bp.route("/add", methods=["GET", "POST"])
@login_required
@admin_required
def add():
    """
    /add
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    classes = class_service.get_all()

    if request.method == "POST":
        mssv = request.form.get("mssv")
        ho_ten = request.form.get("ho_ten")
        lop_id = request.form.get("lop_id", type=int)

        # Xử lý upload ảnh avatar
        avatar_filename = None
        if "avatar" in request.files:
            file = request.files["avatar"]
            if file and file.filename != "" and allowed_image(file.filename):
                ext = file.filename.rsplit(".", 1)[1].lower()
                avatar_filename = f"{mssv}_avatar.{ext}"

                # Tạo thư mục cho sinh viên nếu chưa có
                student_dir = os.path.join(Config.DATABASE_DIR, mssv)
                os.makedirs(student_dir, exist_ok=True)

                # Lưu avatar vào trong luôn (Làm file số 0), xác thực và xóa EXIF
                file_path = os.path.join(student_dir, f"0.{ext}")
                try:
                    save_validated_image(file, file_path)
                    avatar_filename = f"{mssv}/0.{ext}"  # path tương đối
                except Exception as e:
                    flash(f"Lỗi ảnh tải lên: {str(e)}", "danger")
                    return redirect(url_for("students.list_students"))

        data = {
            "mssv": mssv,
            "ho_ten": ho_ten,
            "email": request.form.get("email"),
            "sdt": request.form.get("sdt"),
            "lop_id": lop_id,
            "ngay_sinh": request.form.get("ngay_sinh") or None,
            "gioi_tinh": request.form.get("gioi_tinh", type=int),
            "avatar": avatar_filename,
        }

        result = student_service.create(data)
        if result >= 0:
            flash(f"Thêm sinh viên '{ho_ten}' thành công", "success")
            return redirect(url_for("students.list_students"))
        else:
            flash("Có lỗi xảy ra, có thể MSSV đã tồn tại", "danger")

    return render_template("students/add.html", classes=classes)


@students_bp.route("/api/add", methods=["POST"])
@login_required
def api_add():
    """
    /api/add
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    data = request.json
    mssv = data.get("mssv")
    ho_ten = data.get("ho_ten")
    lop_id = data.get("lop_id")
    images = data.get("images", [])  # array base64

    if not mssv or not ho_ten or not lop_id:
        return jsonify({"success": False, "msg": "Thiếu thông tin bắt buộc"})

    student_data = {
        "mssv": mssv,
        "ho_ten": ho_ten,
        "lop_id": int(lop_id),
        "avatar": (
            f"{mssv}/0.jpg" if images else None
        ),  # Set first image as avatar if available
        "da_train": 0,
        "trang_thai_face": 1,
    }

    # Check if student already exists
    existing = student_service.get_by_mssv(mssv)
    if existing:
        # Update existing student
        update_data = {
            "ho_ten": ho_ten,
            "lop_id": int(lop_id),
            "da_train": 0,
            "trang_thai_face": 1,
        }
        if images:
            update_data["avatar"] = f"{mssv}/0.jpg"

        student_service.update(existing["id"], update_data)
        student_id = existing["id"]
    else:
        # Save new student to db
        student_id = student_service.create(student_data)
        if student_id < 0:
            return jsonify({"success": False, "msg": "Lỗi CSDL khi thêm sinh viên"})

    # Save images to folder
    valid_count = 0
    if images:
        student_dir = os.path.join(Config.DATABASE_DIR, mssv)
        os.makedirs(student_dir, exist_ok=True)
        for idx, base64_str in enumerate(images):
            try:
                # Remove header 'data:image/jpeg;base64,' if exists
                if "," in base64_str:
                    base64_str = base64_str.split(",")[1]
                img_data = base64.b64decode(base64_str)

                # Decode image with OpenCV to check blurriness
                nparr = np.frombuffer(img_data, np.uint8)
                img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if img_cv is not None:
                    # Calculate variance of Laplacian to get blur score
                    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

                    # Threshold: Images with score < 100 are considered blurry
                    if blur_score < 100:
                        print(f"Skipping blurry image {idx} (Score: {blur_score:.2f})")
                        continue  # Bỏ qua ảnh này, không lưu

                # Save valid image
                with open(os.path.join(student_dir, f"{valid_count}.jpg"), "wb") as f:
                    f.write(img_data)
                valid_count += 1
            except Exception as e:
                print(f"Error processing image {idx}: {e}")
                pass

    return jsonify({"success": True, "msg": "Đăng ký khuôn mặt thành công!"})


@students_bp.route("/api/student/<mssv>")
@login_required
def api_get_student(mssv):
    """Lấy thông tin sinh viên theo MSSV để điền tự động"""
    student = student_service.get_by_mssv(mssv)
    if student:
        return jsonify(
            {
                "success": True,
                "data": {"ho_ten": student["ho_ten"], "lop_id": student["lop_id"]},
            }
        )
    return jsonify({"success": False, "msg": "Không tìm thấy sinh viên"})


@students_bp.route("/<int:id>")
@login_required
def detail(id):
    """
    /<int:id>
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    student = student_service.get_by_id(id)
    if not student:
        flash("Không tìm thấy sinh viên", "warning")
        return redirect(url_for("students.list_students"))

    from services.attendance_service import get_student_history

    history = get_student_history(student["mssv"], limit=50)
    image_count = student_service.count_images(student["mssv"])

    return render_template(
        "students/detail.html",
        student=student,
        history=history,
        image_count=image_count,
    )


@students_bp.route("/api/images/<mssv>")
@login_required
def api_images(mssv):
    """
    /api/images/<mssv>
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    student_dir = os.path.join(Config.DATABASE_DIR, mssv)
    if not os.path.exists(student_dir):
        return jsonify([])

    images = []
    for f in os.listdir(student_dir):
        if f.lower().endswith(".jpg") or f.lower().endswith(".png"):
            images.append(f"{mssv}/{f}")

    # Sort them nicely if they are numbered
    images.sort(
        key=lambda x: (
            int(x.split("/")[-1].split(".")[0])
            if x.split("/")[-1].split(".")[0].isdigit()
            else 999
        )
    )
    return jsonify(images)


@students_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit(id):
    """
    /<int:id>/edit
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    student = student_service.get_by_id(id)
    if not student:
        flash("Không tìm thấy sinh viên", "warning")
        return redirect(url_for("students.list_students"))

    classes = class_service.get_all()

    if request.method == "POST":
        data = {
            "ho_ten": request.form.get("ho_ten"),
            "email": request.form.get("email"),
            "sdt": request.form.get("sdt"),
            "lop_id": request.form.get("lop_id", type=int),
            "ngay_sinh": request.form.get("ngay_sinh") or None,
            "gioi_tinh": request.form.get("gioi_tinh", type=int),
        }

        new_pwd = request.form.get("new_password")
        if new_pwd and new_pwd.strip():
            from werkzeug.security import generate_password_hash

            data["password_hash"] = generate_password_hash(
                new_pwd.strip(), method="pbkdf2:sha256"
            )

        # Xử lý upload ảnh mới
        if "avatar" in request.files:
            file = request.files["avatar"]
            if file and file.filename != "" and allowed_image(file.filename):
                mssv = student["mssv"]
                ext = file.filename.rsplit(".", 1)[1].lower()
                student_dir = os.path.join(Config.DATABASE_DIR, mssv)
                os.makedirs(student_dir, exist_ok=True)

                # Ghi đè file 0, xác thực và xóa EXIF
                file_path = os.path.join(student_dir, f"0.{ext}")
                try:
                    save_validated_image(file, file_path)
                    data["avatar"] = f"{mssv}/0.{ext}"
                except Exception as e:
                    flash(f"Lỗi ảnh tải lên: {str(e)}", "danger")
                    return redirect(url_for("students.detail", id=id))

        if student_service.update(id, data):
            flash("Cập nhật thành công", "success")
            return redirect(url_for("students.detail", id=id))
        else:
            flash("Cập nhật thất bại", "danger")

    return render_template("students/edit.html", student=student, classes=classes)


@students_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(id):
    """
    /<int:id>/delete
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    if student_service.delete(id):
        flash("Đã xóa sinh viên", "success")
    else:
        flash("Lỗi khi xóa", "danger")
    return redirect(url_for("students.list_students"))


@students_bp.route("/pending")
@login_required
def pending_faces():
    """
    Danh sách SV đang chờ duyệt khuôn mặt
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
    """
    sql = """
        SELECT sv.id, sv.mssv, sv.ho_ten, sv.avatar, lh.ten_lop 
        FROM sinh_vien sv
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE sv.trang_thai_face = 1
    """
    pending_list = execute_query(sql)
    return render_template("students/pending.html", students=pending_list)


@students_bp.route("/approve-face/<int:id>", methods=["POST"])
@login_required
def approve_face(id):
    """
    Phê duyệt khuôn mặt cho SV
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
    """
    # Cập nhật trạng thái trang_thai_face = 2 (Đã duyệt)
    if execute_update("UPDATE sinh_vien SET trang_thai_face = 2 WHERE id = %s", (id,)):
        flash("Đã phê duyệt khuôn mặt thành công!", "success")
    else:
        flash("Có lỗi khi phê duyệt", "danger")
    return redirect(url_for("students.pending_faces"))


@students_bp.route("/approve-all", methods=["POST"])
@login_required
def approve_all_faces():
    """
    Phê duyệt TẤT CẢ khuôn mặt đang chờ
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
    """
    count = execute_update(
        "UPDATE sinh_vien SET trang_thai_face = 2 WHERE trang_thai_face = 1"
    )
    if count > 0:
        flash(f"Đã phê duyệt thành công {count} sinh viên!", "success")
    else:
        flash("Không có sinh viên nào cần phê duyệt", "info")
    return redirect(url_for("students.pending_faces"))


@students_bp.route("/reject-face/<int:id>", methods=["POST"])
@login_required
def reject_face(id):
    """
    Từ chối khuôn mặt (yêu cầu chụp lại)
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
    """
    # Cập nhật trạng thái trang_thai_face = 3 (Từ chối)
    if execute_update("UPDATE sinh_vien SET trang_thai_face = 3 WHERE id = %s", (id,)):
        flash("Đã từ chối khuôn mặt sinh viên.", "info")
    else:
        flash("Có lỗi xảy ra", "danger")
    return redirect(url_for("students.pending_faces"))


@students_bp.route("/api/send-notification", methods=["POST"])
@login_required
def api_send_notification():
    """
    Gửi thông báo đẩy (Push Notification) cho sinh viên
    ---
    tags:
      - Web API
    """
    data = request.json
    title = data.get("title")
    body = data.get("body")
    mssv_list = data.get("mssv_list", [])

    if not title or not body:
        return jsonify(
            {"success": False, "msg": "Vui lòng nhập đầy đủ Tiêu đề và Nội dung"}
        )

    from services.fcm_service import send_custom_notification

    success_count = send_custom_notification(title, body, mssv_list)

    msg = f"Đã gửi thông báo thành công cho {success_count} thiết bị"
    if not mssv_list:
        msg = f"Đã gửi thông báo cho toàn bộ {success_count} sinh viên (có sử dụng App)"

    return jsonify({"success": True, "msg": msg, "count": success_count})
