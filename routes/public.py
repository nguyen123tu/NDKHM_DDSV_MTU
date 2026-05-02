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
        SELECT DATE_FORMAT(dd.thoi_gian, '%d/%m/%Y %H:%i') as thoi_gian, 
               DATE_FORMAT(dd.gio_ra, '%H:%i') as gio_ra,
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


def _do_recognize(image_data):
    """
    Hàm nhận diện khuôn mặt dùng chung (được gọi từ API public và mobile).
    
    Args:
        image_data: base64 string (có hoặc không có prefix data:image/...)
    
    Returns:
        dict: Kết quả nhận diện, có "success", "student", "similarity", etc.
    """
    import base64
    import cv2
    import numpy as np
    from core.engine import get_engine
    from core.matcher import get_matcher
    
    # Decode base64 → numpy array
    try:
        img_b64 = image_data.split(',')[1] if ',' in image_data else image_data
        img_bytes = base64.b64decode(img_b64)
        img_np = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    except Exception:
        return {"success": False, "msg": "Ảnh không hợp lệ"}
    
    if frame is None:
        return {"success": False, "msg": "Không đọc được ảnh"}
    
    # Nhận diện khuôn mặt
    engine = get_engine()
    face_results = engine['detect_and_embed'](frame)
    
    if len(face_results) == 0:
        return {"success": False, "msg": "Không phát hiện khuôn mặt. Hãy nhìn thẳng vào camera."}
    
    # Lấy khuôn mặt đầu tiên (lớn nhất)
    face = face_results[0]
    embedding = face['embedding']
    
    # So khớp
    matcher = get_matcher()
    mssv, sim = matcher.match(embedding)
    
    if mssv == "UNKNOWN":
        return {
            "success": False, 
            "msg": "Không nhận diện được. Đảm bảo khuôn mặt đã được đăng ký trong hệ thống.",
            "similarity": round(sim, 2)
        }
        
    # --- KIỂM TRA LIVENESS (CHỐNG GIẢ MẠO QUA MÀN HÌNH ĐIỆN THOẠI) ---
    def check_liveness_heuristic(image_frame, bbox):
        x1, y1, x2, y2 = map(int, bbox)
        face_roi = image_frame[max(0,y1):y2, max(0,x1):x2]
        if face_roi.size == 0: return True, ""
        
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # 1. Laplacian Variance (Độ mờ - Ảnh chụp màn hình thường bị mất nét)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 2. Specular Reflection (Độ chói - Màn hình điện thoại phát sáng)
        hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
        v_channel = hsv[:,:,2]
        glare_ratio = np.sum(v_channel > 240) / (v_channel.size + 1e-6)
        
        is_spoof = False
        reason = ""
        
        # Ngưỡng phát hiện
        if blur_score < 10.0:
            is_spoof = True
            reason = f"Ảnh quá mờ ({blur_score:.1f}), nghi ngờ gian lận"
        elif glare_ratio > 0.40: # Hơn 40% diện tích mặt bị chói lóa
            is_spoof = True
            reason = f"Độ lóa cao ({glare_ratio:.2%}), nghi ngờ màn hình"
            
        return not is_spoof, reason

    is_real, spoof_reason = check_liveness_heuristic(frame, face['bbox'])
    if not is_real:
        # Ghi nhận hành vi gian lận vào bảng gian_lan_log
        from db.connection import execute_update
        sv_temp = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,))
        if sv_temp:
            execute_update(
                "INSERT INTO gian_lan_log (sinh_vien_id, loai_gian_lan, chi_tiet) VALUES (%s, %s, %s)",
                (sv_temp['id'], 'Spoofing', f"Phát hiện dùng ảnh giả: {spoof_reason}. Độ trùng khớp: {sim:.2f}")
            )
        return {
            "success": False,
            "msg": f"Cảnh báo: Phát hiện khuôn mặt không hợp lệ ({spoof_reason}). Hành vi đã bị ghi nhận!",
            "similarity": round(sim, 2)
        }
    
    # Lấy thông tin SV
    sv = execute_one("""
        SELECT sv.mssv, sv.ho_ten, sv.email, sv.sdt, sv.avatar, sv.ngay_sinh, sv.gioi_tinh, sv.lop_id,
               lh.ten_lop, lh.ma_lop
        FROM sinh_vien sv
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE sv.mssv = %s
    """, (mssv,))
    
    if not sv:
        return {"success": False, "msg": "Lỗi dữ liệu sinh viên"}
    
    # Xử lý đường dẫn Avatar
    import os
    import glob
    from config import Config
    
    avatar_path = sv.get("avatar")
    
    # Nếu avatar rỗng hoặc đường dẫn không hợp lệ
    if not avatar_path or not os.path.exists(os.path.join(Config.BASE_DIR, avatar_path)):
        # Thử tìm ảnh trong thư mục database/mssv/
        db_path = os.path.join(Config.DATABASE_DIR, mssv)
        images = glob.glob(f"{db_path}/*.jpg") + glob.glob(f"{db_path}/*.png")
        if images:
            # Lấy ảnh đầu tiên làm avatar (1.jpg, 0.jpg, v.v.)
            # Chuyển đổi đường dẫn tuyệt đối thành tương đối để frontend dùng
            avatar_path = f"database/{mssv}/{os.path.basename(images[0])}"
        else:
            avatar_path = None
            
    return {
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
            "do_chinh_xac": round(sim, 4),
            "avatar": avatar_path
        },
    }


@public_bp.route('/api/recognize', methods=['POST'])
def api_recognize():
    """
    API nhận ảnh base64 từ webcam SV, nhận diện khuôn mặt, trả về thông tin.
    
    Request: { "image": "data:image/jpeg;base64,...", "lop_id": 1 }
    Response: { "success": true, "student": {...}, "attendance": {...} }
    """
    from services import attendance_service
    
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"success": False, "msg": "Không có ảnh"})
    
    lop_id = data.get('lop_id')
    
    # Sử dụng hàm nhận diện chung
    recognize_result = _do_recognize(data['image'])
    
    if not recognize_result.get('success'):
        return jsonify(recognize_result)
    
    mssv = recognize_result['student']['mssv']
    sim = recognize_result['similarity']
    sv = recognize_result['student']
    
    # Ghi điểm danh nếu có chọn lớp (hoặc dùng lớp mặc định của SV)
    sv_db = execute_one("SELECT lop_id FROM sinh_vien WHERE mssv = %s", (mssv,))
    check_lop_id = lop_id if lop_id else (sv_db.get('lop_id') if sv_db else None)
    attendance_info = None
    
    # [NEW] Lưu ảnh bằng chứng để chống gian lận (audit trail)
    evidence_path = None
    try:
        import cv2
        import base64
        import numpy as np
        from config import Config
        import os
        import uuid
        from datetime import datetime
        
        img_b64 = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        img_bytes = base64.b64decode(img_b64)
        img_np = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
        
        date_folder = datetime.now().strftime("%Y%m%d")
        save_dir = os.path.join(Config.EVIDENCE_DIR, date_folder)
        os.makedirs(save_dir, exist_ok=True)
        
        filename = f"kiosk_{mssv}_{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
        abs_path = os.path.join(save_dir, filename)
        cv2.imwrite(abs_path, frame)
        rel_path = os.path.relpath(abs_path, Config.BASE_DIR).replace('\\', '/')
        evidence_path = f"EVIDENCE:{rel_path}"
    except Exception as e:
        print(f"[KIOSK] Lỗi lưu bằng chứng: {e}")

    if check_lop_id:
        log_result = attendance_service.log(
            mssv=mssv, 
            lop_id=check_lop_id, 
            do_chinh_xac=sim, 
            camera_id=0,
            ghi_chu=evidence_path
        )
        if log_result and isinstance(log_result, dict):
            status_msg = "Điểm danh vào thành công!"
            if log_result['action'] == 'checkout':
                status_msg = "Hẹn gặp lại! Đã ghi nhận giờ ra."
            elif log_result['action'] == 'skip':
                status_msg = "Bạn đã điểm danh trước đó rồi."
                
            attendance_info = {
                'action': log_result['action'],
                'msg': status_msg
            }
    
    # Lấy lịch sử hôm nay
    today_records = execute_query("""
        SELECT DATE_FORMAT(dd.thoi_gian, '%H:%i') as gio_vao,
               DATE_FORMAT(dd.gio_ra, '%H:%i') as gio_ra,
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
        "bbox": recognize_result.get('bbox'),
        "student": sv,
        "attendance": attendance_info,
        "today_records": today_records
    })

