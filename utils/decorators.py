"""
Utils: Decorators cho Flask routes.
Bảo vệ routes bằng @login_required và @admin_required.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request


def login_required(f):
    """
    Decorator kiểm tra xem người dùng đã đăng nhập chưa.
    Nếu chưa -> trả về JSON 401 (với API/AJAX) hoặc redirect về login.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            if (
                request.is_json
                or request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.path.startswith("/api/")
                or (
                    request.path.startswith("/chatbot/")
                    and request.endpoint != "chatbot.chat_page"
                )
            ):
                return {
                    "success": False,
                    "message": "Unauthorized: Vui lòng đăng nhập",
                }, 401
            flash("Vui lòng đăng nhập để truy cập trang này.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Decorator kiểm tra quyền admin.
    Phải đặt sau @login_required.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get("admin_role", "")
        if role != "admin":
            if (
                request.is_json
                or request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.path.startswith("/api/")
                or request.path.startswith("/chatbot/")
            ):
                return {
                    "success": False,
                    "message": "Forbidden: Yêu cầu quyền Quản trị (Admin)",
                }, 403
            flash("Bạn không có quyền truy cập chức năng này.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)

    return decorated_function


def api_key_required(f):
    """
    Decorator cho public API endpoints (nếu cần xác thực Ứng dụng client).
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Implement API key verification logic here
        pass
        return f(*args, **kwargs)

    return decorated_function
