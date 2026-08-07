"""
Route Quản lý Tài khoản (Users / Giảng viên)
"""

from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from . import users_bp
from utils.decorators import login_required, admin_required
from db.connection import execute_query, execute_update, execute_one
from services.class_service import get_all as get_all_classes

@users_bp.route("/")
@login_required
@admin_required
def list_users():
    """
    Hiển thị danh sách các tài khoản (Admin / Giảng viên / Sinh viên).
    """
    # Lấy Admin & Giảng viên
    admin_sql = "SELECT id, username, ho_ten, role, created_at FROM admin ORDER BY role ASC, id DESC"
    admin_users = execute_query(admin_sql)
    
    # Lấy Sinh viên
    student_sql = """
        SELECT sv.id, sv.mssv as username, sv.ho_ten, lh.ten_lop, sv.created_at, sv.da_train
        FROM sinh_vien sv
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        ORDER BY sv.id DESC
    """
    student_users = execute_query(student_sql)
    
    # Lấy lớp học cho dropdown
    classes = get_all_classes()
    
    return render_template("users/list.html", admin_users=admin_users, student_users=student_users, classes=classes)


@users_bp.route("/add", methods=["POST"])
@login_required
@admin_required
def add():
    """
    Thêm tài khoản mới (Admin / Giảng viên / Sinh viên).
    """
    role = request.form.get("role", "giang_vien")
    password = request.form.get("password")
    ho_ten = request.form.get("ho_ten")
    
    if not password or not ho_ten:
        flash("Vui lòng điền đầy đủ thông tin", "warning")
        return redirect(url_for("users.list_users"))
        
    pw_hash = generate_password_hash(password, method='pbkdf2:sha256')

    if role == "sinh_vien":
        username = request.form.get("username") # Dùng như MSSV
        lop_id = request.form.get("lop_id")
        if not username or not lop_id:
            flash("Vui lòng nhập MSSV và chọn lớp học", "warning")
            return redirect(url_for("users.list_users"))
            
        existing = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (username,))
        if existing:
            flash("MSSV đã tồn tại", "danger")
            return redirect(url_for("users.list_users"))
            
        sql = "INSERT INTO sinh_vien (mssv, password_hash, ho_ten, lop_id, trang_thai, da_train) VALUES (%s, %s, %s, %s, 1, 0)"
        result = execute_update(sql, (username, pw_hash, ho_ten, lop_id))
        
    else:
        username = request.form.get("username")
        if not username:
            flash("Vui lòng nhập tên đăng nhập", "warning")
            return redirect(url_for("users.list_users"))
            
        existing = execute_one("SELECT id FROM admin WHERE username = %s", (username,))
        if existing:
            flash("Tên đăng nhập đã tồn tại", "danger")
            return redirect(url_for("users.list_users"))

        sql = "INSERT INTO admin (username, password_hash, ho_ten, role) VALUES (%s, %s, %s, %s)"
        result = execute_update(sql, (username, pw_hash, ho_ten, role))

    if result >= 0:
        flash(f"Đã thêm tài khoản '{username}' thành công", "success")
    else:
        flash("Có lỗi khi thêm tài khoản", "danger")

    return redirect(url_for("users.list_users"))


@users_bp.route("/<role>/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete(role, id):
    """
    Xóa tài khoản theo role.
    """
    from flask import session

    if role in ["admin", "giang_vien"]:
        if id == session.get("admin_id"):
            flash("Không thể tự xóa tài khoản của chính mình", "danger")
            return redirect(url_for("users.list_users"))
        result = execute_update("DELETE FROM admin WHERE id = %s", (id,))
    elif role == "sinh_vien":
        result = execute_update("DELETE FROM sinh_vien WHERE id = %s", (id,))
    else:
        flash("Role không hợp lệ", "danger")
        return redirect(url_for("users.list_users"))

    if result >= 0:
        flash("Đã xóa tài khoản", "info")
    else:
        flash("Lỗi khi xóa tài khoản", "danger")

    return redirect(url_for("users.list_users"))


@users_bp.route("/<role>/<int:id>/reset_password", methods=["POST"])
@login_required
@admin_required
def reset_password(role, id):
    """
    Đổi mật khẩu tài khoản.
    """
    new_password = request.form.get("new_password")
    if not new_password:
        flash("Vui lòng nhập mật khẩu mới", "warning")
        return redirect(url_for("users.list_users"))
        
    pw_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    
    if role in ["admin", "giang_vien"]:
        result = execute_update("UPDATE admin SET password_hash = %s WHERE id = %s", (pw_hash, id))
    elif role == "sinh_vien":
        result = execute_update("UPDATE sinh_vien SET password_hash = %s WHERE id = %s", (pw_hash, id))
    else:
        flash("Role không hợp lệ", "danger")
        return redirect(url_for("users.list_users"))
        
    if result >= 0:
        flash("Đã đổi mật khẩu thành công", "success")
    else:
        flash("Lỗi khi đổi mật khẩu", "danger")
        
    return redirect(url_for("users.list_users"))
