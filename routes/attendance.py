"""
Route Điểm Danh Realtime
"""

from flask import render_template, jsonify, request, current_app, session
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
        {'id': 'http://192.168.1.158', 'name': 'ESP32 Cam (Luồng video :80)'},
        {'id': 'rtsp://admin:L2F0C994@192.168.1.108/cam/realmonitor?channel=1&subtype=1', 'name': '📹 Camera IMOU (Cắm dây LAN)'},
        {'id': 'rtsp://admin:L2F0C994@192.168.1.80:554/cam/realmonitor?channel=1&subtype=0', 'name': '📹 Camera IMOU (Không Dây WAN)'},
        {'id': 'custom', 'name': '🌐 Camera IP / RTSP tuỳ chỉnh (Khác)'}
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
    start_time = data.get('start_time', '07:00')
    
    if not lop_id:
        return jsonify({"success": False, "msg": "Thiếu thông tin lớp"}), 400
        
    socketio = current_app.extensions['socketio']
    admin_id = session.get('admin_id')
    phien_id = start_session(lop_id, camera_id, socketio, start_time, admin_id=admin_id)
    if phien_id:
        return jsonify({"success": True, "session_id": phien_id})
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
    admin_id = session.get('admin_id')
    result = stop_session(admin_id=admin_id)
    if isinstance(result, dict):
        return jsonify({"success": True, "data": result})
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

@attendance_bp.route('/leave-requests')
@login_required
def list_leave_requests():
    """Trang quản lý đơn xin phép của sinh viên"""
    status = request.args.get('status', type=int)
    from services.leave_service import get_all_leave_requests
    reqs = get_all_leave_requests(status)
    return render_template('attendance/leave_requests.html', requests=reqs, current_status=status)

@attendance_bp.route('/approve-leave/<int:request_id>', methods=['POST'])
@login_required
def approve_leave(request_id):
    """API duyệt đơn xin phép"""
    from services.leave_service import update_leave_status
    if update_leave_status(request_id, 1) > 0:
        return jsonify({"success": True, "message": "Đã duyệt đơn"})
    return jsonify({"success": False, "message": "Lỗi cập nhật"})

@attendance_bp.route('/reject-leave/<int:request_id>', methods=['POST'])
@login_required
def reject_leave(request_id):
    """API từ chối đơn xin phép"""
    from services.leave_service import update_leave_status
    if update_leave_status(request_id, 2) > 0:
        return jsonify({"success": True, "message": "Đã từ chối đơn"})
    return jsonify({"success": False, "message": "Lỗi cập nhật"})

