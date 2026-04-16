"""
Route Điểm Danh Realtime
"""

from flask import render_template, jsonify, request, current_app
from . import attendance_bp
from utils.decorators import login_required
from services import class_service, attendance_service
from services.recognition_thread import start_session, stop_session, get_active_session

@attendance_bp.route('/live')
@login_required
def live():
    classes = class_service.get_all()
    # Danh sách camera test tạm, sau này sẽ lấy từ DB/CameraManager
    cameras = [{'id': 0, 'name': 'USB Camera Default'}]
    
    active = get_active_session()
    current_class = active.lop_id if active and active.is_running else None
    
    return render_template('attendance/live.html', 
                          classes=classes, 
                          cameras=cameras,
                          current_class=current_class)

@attendance_bp.route('/start', methods=['POST'])
@login_required
def start():
    lop_id = request.json.get('lop_id')
    camera_id = request.json.get('camera_id', 0)
    
    if not lop_id:
        return jsonify({"success": False, "msg": "Thiếu thông tin lớp"}), 400
        
    socketio = current_app.extensions['socketio']
    if start_session(lop_id, camera_id, socketio):
        return jsonify({"success": True})
    return jsonify({"success": False, "msg": "Không thể khởi động camera"}), 500

@attendance_bp.route('/stop', methods=['POST'])
@login_required
def stop():
    stop_session()
    return jsonify({"success": True})

@attendance_bp.route('/history')
@login_required
def history():
    classes = class_service.get_all(active_only=False)
    
    lop_id = request.args.get('lop_id', type=int)
    date = request.args.get('date')
    mssv = request.args.get('mssv')
    page = request.args.get('page', 1, type=int)
    
    data = attendance_service.get_history(lop_id=lop_id, date=date, mssv=mssv, page=page)
    
    return render_template('attendance/history.html', 
                          history=data['items'],
                          pagination=data,
                          classes=classes,
                          current_lop_id=lop_id,
                          current_date=date,
                          current_mssv=mssv)

@attendance_bp.route('/api/today-stats')
@login_required
def api_today_stats():
    lop_id = request.args.get('lop_id', type=int)
    stats = attendance_service.get_today_summary(lop_id)
    return jsonify(stats)
