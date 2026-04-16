"""
Route Public (Tra cứu không cần đăng nhập)
"""

from flask import render_template, request, jsonify
from . import public_bp
from db.connection import execute_one, execute_query

@public_bp.route('/lookup')
def lookup():
    """Trang tra cứu thông tin điểm danh public (chuẩn Glassmorphism)"""
    return render_template('public/attendance_public.html')

@public_bp.route('/api/lookup', methods=['POST'])
def api_lookup():
    """API để JS gọi từ trang public"""
    mssv = request.json.get('mssv')
    if not mssv:
        return jsonify({"success": False, "msg": "Vui lòng nhập MSSV"})
        
    # Tìm SV
    sv = execute_one("""
        SELECT sv.ho_ten, lh.ten_lop 
        FROM sinh_vien sv 
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE sv.mssv = %s
    """, (mssv,))
    
    if not sv:
        return jsonify({"success": False, "msg": "Không tìm thấy sinh viên"})
        
    # Lấy lịch sử 10 lần gần nhất
    history = execute_query("""
        SELECT DATE_FORMAT(dd.thoi_gian, '%%d/%%m/%%Y %%H:%%i') as thoi_gian, 
               DATE_FORMAT(dd.gio_ra, '%%H:%%i') as gio_ra,
               dd.trang_thai, 
               lh.ten_lop 
        FROM diem_danh dd
        LEFT JOIN lop_hoc lh ON dd.lop_id = lh.id
        WHERE dd.sinh_vien_id = (SELECT id FROM sinh_vien WHERE mssv = %s)
        ORDER BY dd.thoi_gian DESC LIMIT 10
    """, (mssv,))
    
    return jsonify({
        "success": True,
        "student": {
            "mssv": mssv,
            "ho_ten": sv["ho_ten"],
            "ten_lop": sv["ten_lop"] or "Chưa phân lớp"
        },
        "history": history
    })


# ================================================================
# TRANG TỰ ĐIỂM DANH BẰNG WEBCAM (Dành cho Sinh Viên)
# ================================================================

@public_bp.route('/selfcheck')
def selfcheck():
    """Trang sinh viên tự điểm danh bằng webcam."""
    # Lấy danh sách lớp để SV chọn
    classes = execute_query("SELECT id, ma_lop, ten_lop FROM lop_hoc WHERE trang_thai = 1 ORDER BY ma_lop")
    return render_template('public/selfcheck.html', classes=classes)


@public_bp.route('/api/recognize', methods=['POST'])
def api_recognize():
    """
    API nhận ảnh base64 từ webcam SV, nhận diện khuôn mặt, trả về thông tin.
    
    Request: { "image": "data:image/jpeg;base64,...", "lop_id": 1 }
    Response: { "success": true, "student": {...}, "attendance": {...} }
    """
    import base64
    import cv2
    import numpy as np
    from core.engine import get_engine
    from core.matcher import get_matcher
    from services import student_service, attendance_service
    
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"success": False, "msg": "Không có ảnh"})
    
    lop_id = data.get('lop_id')
    
    # Decode base64 → numpy array
    try:
        img_b64 = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        img_bytes = base64.b64decode(img_b64)
        img_np = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    except Exception:
        return jsonify({"success": False, "msg": "Ảnh không hợp lệ"})
    
    if frame is None:
        return jsonify({"success": False, "msg": "Không đọc được ảnh"})
    
    # Nhận diện khuôn mặt
    engine = get_engine()
    face_results = engine['detect_and_embed'](frame)
    
    if len(face_results) == 0:
        return jsonify({"success": False, "msg": "Không phát hiện khuôn mặt. Hãy nhìn thẳng vào camera."})
    
    # Lấy khuôn mặt đầu tiên (lớn nhất)
    face = face_results[0]
    embedding = face['embedding']
    
    # So khớp
    matcher = get_matcher()
    mssv, sim = matcher.match(embedding)
    
    if mssv == "UNKNOWN":
        return jsonify({
            "success": False, 
            "msg": "Không nhận diện được. Đảm bảo khuôn mặt đã được đăng ký trong hệ thống.",
            "similarity": round(sim, 2)
        })
    
    # Lấy thông tin SV
    sv = execute_one("""
        SELECT sv.mssv, sv.ho_ten, sv.email, sv.sdt, sv.avatar, sv.ngay_sinh, sv.gioi_tinh, sv.lop_id,
               lh.ten_lop, lh.ma_lop
        FROM sinh_vien sv
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE sv.mssv = %s
    """, (mssv,))
    
    if not sv:
        return jsonify({"success": False, "msg": "Lỗi dữ liệu sinh viên"})
    
    # Ghi điểm danh nếu có chọn lớp (hoặc dùng lớp mặc định của SV)
    check_lop_id = lop_id if lop_id else sv.get('lop_id')
    attendance_info = None
    if check_lop_id:
        log_result = attendance_service.log(
            mssv=mssv, lop_id=check_lop_id, do_chinh_xac=sim, camera_id=0
        )
        if log_result and isinstance(log_result, dict):
            attendance_info = {
                'action': log_result['action'],
                'msg': 'Điểm danh vào thành công!' if log_result['action'] == 'checkin' else 'Ghi nhận giờ ra!'
            }
    
    # Lấy lịch sử hôm nay
    today_records = execute_query("""
        SELECT DATE_FORMAT(dd.thoi_gian, '%%H:%%i') as gio_vao,
               DATE_FORMAT(dd.gio_ra, '%%H:%%i') as gio_ra,
               dd.trang_thai, dd.do_chinh_xac,
               lh.ten_lop
        FROM diem_danh dd
        LEFT JOIN lop_hoc lh ON dd.lop_id = lh.id
        WHERE dd.sinh_vien_id = (SELECT id FROM sinh_vien WHERE mssv = %s)
          AND DATE(dd.thoi_gian) = CURDATE()
        ORDER BY dd.thoi_gian DESC
    """, (mssv,))
    
    return jsonify({
        "success": True,
        "similarity": round(sim, 2),
        "bbox": [int(x) for x in face['bbox']],
        "student": {
            "mssv": sv["mssv"],
            "ho_ten": sv["ho_ten"],
            "email": sv.get("email", ""),
            "sdt": sv.get("sdt", ""),
            "ten_lop": sv.get("ten_lop", "Chưa phân lớp"),
            "ma_lop": sv.get("ma_lop", ""),
            "gioi_tinh": "Nam" if sv.get("gioi_tinh") == 1 else "Nữ",
        },
        "attendance": attendance_info,
        "today_records": today_records
    })

