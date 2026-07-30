"""
Mobile Sync API routes (offline-first synchronization).
"""
import json
from datetime import datetime
from flask import request, jsonify
from db.connection import execute_one, execute_query, execute_update
from . import api_mobile_bp
from .helpers import _require_mobile_auth


@api_mobile_bp.route('/sync/students', methods=['GET'])
def pull_students():
    """
    Đồng bộ (Pull) dữ liệu sinh viên từ Server xuống App.
    """
    _, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    last_sync_time_str = request.args.get('last_sync_time', '1970-01-01 00:00:00')
    try:
        last_sync_time = datetime.strptime(last_sync_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({"success": False, "message": "Sai định dạng thời gian"}), 400

    try:
        sql = """
            SELECT sv.id, sv.mssv, sv.ho_ten, sv.face_vector, sv.updated_at, sv.trang_thai
            FROM sinh_vien sv
            WHERE sv.updated_at >= %s
        """
        students = execute_query(sql, (last_sync_time,))
        
        for sv in students:
            if 'updated_at' in sv and sv['updated_at']:
                sv['updated_at'] = sv['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            if sv.get('face_vector'):
                try:
                    sv['face_vector'] = json.loads(sv['face_vector'])
                except:
                    sv['face_vector'] = None

        return jsonify({
            "success": True,
            "data": students,
            "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sync/attendance', methods=['POST'])
def push_attendance():
    """
    Đồng bộ (Push) dữ liệu điểm danh Offline từ App lên Server.
    Sử dụng record_attendance() với client_event_id chống trùng.
    """
    _, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    logs = data.get('logs', [])
    
    if not logs:
        return jsonify({"success": False, "message": "Không có dữ liệu điểm danh"}), 400

    synced_uuids = []
    errors = []

    for log in logs:
        local_uuid = log.get('local_uuid')
        mssv = log.get('mssv')
        session_id = log.get('session_id')
        check_time = log.get('check_time')
        confidence = float(log.get('confidence') or 0.0)
        lat = log.get('lat')
        lng = log.get('lng')

        if not local_uuid or not mssv:
            errors.append({"local_uuid": local_uuid, "error": "Thiếu dữ liệu"})
            continue

        try:
            # Tìm sinh viên
            sv = execute_one("SELECT id, lop_id FROM sinh_vien WHERE mssv = %s", (mssv,))
            if not sv:
                errors.append({"local_uuid": local_uuid, "error": "Sinh viên không tồn tại"})
                continue

            # Nếu không có session_id, thử tìm phiên đang mở cho lớp
            if not session_id:
                active_sess = execute_one(
                    "SELECT TOP 1 id FROM phien_diem_danh WHERE lop_id = %s AND trang_thai = 1 AND ISNULL(is_cancelled, 0) = 0 ORDER BY id DESC",
                    (sv['lop_id'],)
                )
                if active_sess:
                    session_id = active_sess['id']

            if not session_id:
                errors.append({"local_uuid": local_uuid, "error": "Không tìm thấy phiên điểm danh phù hợp"})
                continue

            from services import attendance_service
            result = attendance_service.record_attendance(
                session_id=session_id,
                student_id=sv['id'],
                method="MOBILE_GPS",
                confidence=confidence,
                latitude=lat,
                longitude=lng,
                client_event_id=local_uuid,
            )

            if result and (result.get('success') or result.get('action') == 'observed' or result.get('error_code') == 'DUPLICATE_EVENT'):
                synced_uuids.append(local_uuid)
            else:
                errors.append({"local_uuid": local_uuid, "error": result.get('message', 'Lỗi không xác định') if result else 'Lỗi'})
                
        except Exception as e:
            errors.append({"local_uuid": local_uuid, "error": str(e)})

    return jsonify({
        "success": True,
        "synced_local_uuids": synced_uuids,
        "errors": errors
    }), 200


@api_mobile_bp.route('/sync/sessions', methods=['GET'])
def sync_sessions():
    """
    Đồng bộ (Pull) phiên điểm danh đang mở về App.
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    try:
        execute_update(
            "UPDATE phien_diem_danh SET trang_thai = 0, ket_thuc = GETDATE() WHERE trang_thai = 1 AND het_han IS NOT NULL AND het_han < GETDATE()"
        )

        role = payload.get('role', 'admin')
        user_id = payload.get('sub')

        if role == 'student':
            student = execute_one("SELECT lop_id, mssv FROM sinh_vien WHERE id = %s", (user_id,))
            student_mssv = student['mssv'] if student else ''

            sql = """
                SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.het_han, p.trang_thai,
                       l.ma_lop, l.ten_lop, l.giao_vien,
                       (SELECT COUNT(*) FROM diem_danh d 
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND d.status IN ('PRESENT', 'LATE')) as so_da_diem_danh,
                       (SELECT COUNT(*) FROM diem_danh d 
                        JOIN sinh_vien sv2 ON d.sinh_vien_id = sv2.id
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND sv2.mssv = %s) as da_diem_danh_chua
                FROM phien_diem_danh p
                JOIN lop_hoc l ON p.lop_id = l.id
                WHERE p.trang_thai = 1
                ORDER BY p.bat_dau DESC
            """
            sessions = execute_query(sql, (student_mssv,))
        else:
            sql = """
                SELECT p.id, p.lop_id, p.mo_ta, p.bat_dau, p.het_han, p.trang_thai,
                       l.ma_lop, l.ten_lop, l.giao_vien,
                       (SELECT COUNT(DISTINCT d.sinh_vien_id) FROM diem_danh d 
                        WHERE d.lop_id = p.lop_id AND d.thoi_gian >= p.bat_dau 
                        AND d.status IN ('PRESENT', 'LATE')) as so_da_diem_danh,
                       (SELECT COUNT(*) FROM sinh_vien sv WHERE sv.lop_id = p.lop_id AND sv.trang_thai = 1) as tong_sv
                FROM phien_diem_danh p
                JOIN lop_hoc l ON p.lop_id = l.id
                WHERE p.trang_thai = 1
                ORDER BY p.bat_dau DESC
            """
            sessions = execute_query(sql)

        for s in sessions:
            if s.get('bat_dau') and hasattr(s['bat_dau'], 'strftime'):
                s['bat_dau'] = s['bat_dau'].strftime('%Y-%m-%d %H:%M:%S')
            if s.get('het_han') and hasattr(s['het_han'], 'strftime'):
                s['het_han'] = s['het_han'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            "success": True,
            "data": sessions,
            "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sync/schedule', methods=['GET'])
def sync_schedule():
    """
    Đồng bộ (Pull) lịch học về App cho sinh viên.
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    if payload.get('role') != 'student':
        return jsonify({"success": True, "data": [], "message": "Chỉ sinh viên mới có lịch học"}), 200

    user_id = payload.get('sub')
    student = execute_one("SELECT lop_id FROM sinh_vien WHERE id = %s", (user_id,))

    if not student or not student['lop_id']:
        return jsonify({"success": True, "data": []}), 200

    try:
        sql = "SELECT * FROM lich_hoc WHERE lop_id = %s ORDER BY thu ASC, gio_bat_dau ASC"
        schedules = execute_query(sql, (student['lop_id'],))
        return jsonify({
            "success": True,
            "data": schedules,
            "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/sync/notifications', methods=['GET'])
def sync_notifications():
    """
    Đồng bộ (Pull) thông báo về App.
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    user_id = payload.get('sub')
    role = payload.get('role')

    try:
        if role == 'student':
            sql = """
                SELECT TOP 50 id, tieu_de, noi_dung, da_doc, created_at 
                FROM thong_bao 
                WHERE sinh_vien_id = %s 
                ORDER BY created_at DESC
            """
            notifications = execute_query(sql, (user_id,))
        else:
            sql = """
                SELECT TOP 50 id, tieu_de, noi_dung, da_doc, created_at 
                FROM thong_bao 
                ORDER BY created_at DESC
            """
            notifications = execute_query(sql)

        for n in notifications:
            if n.get('created_at') and hasattr(n['created_at'], 'strftime'):
                n['created_at'] = n['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            "success": True,
            "data": notifications,
            "server_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
