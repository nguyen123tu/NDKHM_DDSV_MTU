"""
Route Quản lý Tài khoản (Users / Giảng viên)
"""

from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from . import users_bp
from utils.decorators import login_required, admin_required
from db.connection import execute_query, execute_update, execute_one

@users_bp.route('/')
@login_required
@admin_required
def list_users():
    """
    Hiển thị danh sách các tài khoản (Admin / Giảng viên).
    """
    sql = "SELECT id, username, ho_ten, role, created_at FROM admin ORDER BY role ASC, id DESC"
    users = execute_query(sql)
    return render_template('users/list.html', users=users)

@users_bp.route('/add', methods=['POST'])
@login_required
@admin_required
def add():
    """
    Thêm tài khoản mới (thường là Giảng viên).
    """
    username = request.form.get('username')
    password = request.form.get('password')
    ho_ten = request.form.get('ho_ten')
    role = request.form.get('role', 'giang_vien')
    
    if not username or not password or not ho_ten:
        flash("Vui lòng điền đầy đủ thông tin", "warning")
        return redirect(url_for('users.list_users'))
        
    # Check if username exists
    existing = execute_one("SELECT id FROM admin WHERE username = %s", (username,))
    if existing:
        flash("Tên đăng nhập đã tồn tại", "danger")
        return redirect(url_for('users.list_users'))
        
    pw_hash = generate_password_hash(password)
    
    sql = "INSERT INTO admin (username, password_hash, ho_ten, role) VALUES (%s, %s, %s, %s)"
    result = execute_update(sql, (username, pw_hash, ho_ten, role))
    
    if result >= 0:
        flash(f"Đã thêm tài khoản '{username}' thành công", "success")
    else:
        flash("Có lỗi khi thêm tài khoản", "danger")
        
    return redirect(url_for('users.list_users'))

@users_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(id):
    """
    Xóa tài khoản.
    """
    from flask import session
    # Không cho phép tự xóa tài khoản đang đăng nhập
    if id == session.get('admin_id'):
        flash("Không thể tự xóa tài khoản của chính mình", "danger")
        return redirect(url_for('users.list_users'))
        
    result = execute_update("DELETE FROM admin WHERE id = %s", (id,))
    if result >= 0:
        flash("Đã xóa tài khoản", "info")
    else:
        flash("Lỗi khi xóa tài khoản", "danger")
        
    return redirect(url_for('users.list_users'))
