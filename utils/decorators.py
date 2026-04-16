"""
Utils: Decorators cho Flask routes.
Bảo vệ routes bằng @login_required và @admin_required.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required(f):
    """
    Decorator kiểm tra xem người dùng đã đăng nhập chưa.
    Nếu chưa (không có admin_id trong session) -> redirect về trang login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Vui lòng đăng nhập để truy cập trang này.", "warning")
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator kiểm tra quyền admin.
    Phải đặt sau @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('admin_role', '')
        if role != 'admin':
            flash("Bạn không có quyền truy cập chức năng này.", "danger")
            return redirect(url_for('dashboard.index'))
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
