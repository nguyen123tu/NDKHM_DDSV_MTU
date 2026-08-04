"""
Package routes.mobile - Khởi tạo Blueprint và import các submodule API mobile.
"""

from flask import Blueprint

# Khởi tạo Blueprint cho toàn bộ API Mobile
api_mobile_bp = Blueprint("api_mobile", __name__, url_prefix="/api/mobile")

# Import tất cả các submodules để đăng ký các route với api_mobile_bp
from . import auth, attendance, sessions, sync, students, admin
