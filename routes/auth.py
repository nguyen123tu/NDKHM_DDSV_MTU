"""
Route Đăng nhập và Đăng xuất (Authentication)
"""

from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from urllib.parse import urlparse, urljoin
from . import auth_bp
from db.connection import execute_one
from core.limiter import limiter


def is_safe_url(target):
    """Kiểm tra URL có thuộc cùng host không, ngăn chặn Open Redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("100 per hour")
@limiter.limit("30 per minute")
def login():
    """
    /login
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    # Nếu đã login thì redirect thẳng vào dashboard
    if "admin_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Query user (admin or giang_vien)
        admin = execute_one("SELECT * FROM admin WHERE username = %s", (username,))

        if admin and check_password_hash(admin["password_hash"], password):
            # Lưu session
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            session["admin_role"] = admin["role"]
            session["admin_name"] = admin["ho_ten"]

            flash("Đăng nhập thành công", "success")

            # Xử lý tham số 'next' an toàn (chống Open Redirect)
            next_url = request.args.get("next")
            if next_url and is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for("dashboard.index"))
        else:
            flash("Sai tài khoản hoặc mật khẩu", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    """
    /logout
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    session.clear()
    flash("Đã đăng xuất", "info")
    return redirect(url_for("auth.login"))
