"""
Route Dashboard (Trang chủ Admin)
"""

from flask import render_template, jsonify
from . import dashboard_bp
from utils.decorators import login_required
from services.attendance_service import get_today_summary, get_weekly_chart_data, get_top_absent_students
from services.student_service import get_all as get_all_students
from services.class_service import get_all as get_all_classes

from db.connection import execute_one as db_execute_one

@dashboard_bp.route('/')
@login_required
def index():
    # Lấy thông kê hôm nay
    today_stats = get_today_summary()
    
    # Lấy tổng quan hệ thống (dùng hàm count cơ bản)
    total_students = get_all_students(per_page=1)['total']
    total_classes = len(get_all_classes())
    
    # Lấy top sinh viên vắng nhiều nhất (30 ngày gần nhất)
    top_absent = get_top_absent_students(limit=5)
    
    # Lấy số lượng sinh viên chờ duyệt khuôn mặt
    pending_row = db_execute_one("SELECT COUNT(*) as count FROM sinh_vien WHERE trang_thai_face = 1")
    total_pending = pending_row['count'] if pending_row else 0
    
    return render_template('dashboard/index.html',
                          today_stats=today_stats,
                          total_students=total_students,
                          total_classes=total_classes,
                          top_absent=top_absent,
                          total_pending=total_pending)

@dashboard_bp.route('/api/weekly-chart')
@login_required
def weekly_chart():
    """API trả về dữ liệu vẽ biểu đồ Chart.js"""
    data = get_weekly_chart_data()
    return jsonify(data)

@dashboard_bp.route('/kiosk')
@login_required
def kiosk():
    """Trạm điểm danh chuyên nghiệp (Kiosk Mode)"""
    return render_template('dashboard/kiosk.html')
