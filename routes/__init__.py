"""
Blueprints cho toàn hệ thống.
File này dùng để import và register các routes.
"""

from flask import Blueprint

# Khởi tạo các Blueprints (sẽ được register trong app.py)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')
students_bp = Blueprint('students', __name__, url_prefix='/students')
classes_bp = Blueprint('classes', __name__, url_prefix='/classes')
attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')
training_bp = Blueprint('training', __name__, url_prefix='/training')
camera_mgmt_bp = Blueprint('camera_mgmt', __name__, url_prefix='/cameras')
export_bp = Blueprint('export', __name__, url_prefix='/export')
public_bp = Blueprint('public', __name__, url_prefix='/public')

# Import các file route để register chức năng
from . import auth, dashboard, students, classes, attendance, training, camera_mgmt, export, public
