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
    """
    /live
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
    # Danh sách camera test tạm, sau này sẽ lấy từ DB/CameraManager
    cameras = [
        {'id': 0, 'name': 'USB Camera Default'},
        {'id': 'http://192.168.1.158:81/stream', 'name': 'ESP32 Cam (Luồng video :81)'},
        {'id': 'http://192.168.1.158', 'name': 'ESP32 Cam (Luồng video :80)'}
    ]
    
    active = get_active_session()
    current_class = active.lop_id if active and active.is_running else None
    
    return render_template('attendance/live.html', 
                          classes=classes, 
                          cameras=cameras,
                          current_class=current_class)

@attendance_bp.route('/start', methods=['POST'])
@login_required
def start():
    """
    /start
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    data = request.json or {}
    lop_id = data.get('lop_id')
    camera_id = data.get('camera_id', 0)
    
    if not lop_id:
        return jsonify({"success": False, "msg": "Thiếu thông tin lớp"}), 400
        
    socketio = current_app.extensions['socketio']
    if start_session(lop_id, camera_id, socketio):
        return jsonify({"success": True})
    return jsonify({"success": False, "msg": "Không thể khởi động camera"}), 500

@attendance_bp.route('/stop', methods=['POST'])
@login_required
def stop():
    """
    /stop
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    stop_session()
    return jsonify({"success": True})

@attendance_bp.route('/history')
@login_required
def history():
    """
    /history
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
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
    """
    /api/today-stats
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    lop_id = request.args.get('lop_id', type=int)
    stats = attendance_service.get_today_summary(lop_id)
    return jsonify(stats)
