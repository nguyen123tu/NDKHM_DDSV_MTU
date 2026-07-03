"""
Route Public (Tra cứu không cần đăng nhập)
"""

from flask import render_template, request, jsonify
from . import public_bp
from db.connection import execute_one, execute_query, execute_update

@public_bp.route('/lookup')
def lookup():
    """
    Trang tra cứu thông tin điểm danh public (chuẩn Glassmorphism)
    ---
    tags:
      - Kiosk Public API
    responses:
      200:
        description: Thành công
    """
    return render_template('public/attendance_public.html')

@public_bp.route('/api/lookup', methods=['POST'])
def api_lookup():
    """
    API để JS gọi từ trang public
    """
    import os
    import glob
    from config import Config
    
    mssv = request.json.get('mssv')
    if not mssv:
        return jsonify({"success": False, "msg": "Vui lòng nhập MSSV"})
        
    # Tìm SV
    sv = execute_one("""
        SELECT sv.id, sv.ho_ten, sv.email, sv.sdt, sv.ngay_sinh, sv.gioi_tinh, sv.avatar, lh.ten_lop 
        FROM sinh_vien sv 
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE sv.mssv = %s
    """, (mssv,))
    
    if not sv:
        return jsonify({"success": False, "msg": "Không tìm thấy sinh viên"})
        
    # Lấy lịch sử 10 lần gần nhất
    history = execute_query("""
        SELECT TOP 10 FORMAT(dd.thoi_gian, 'dd/MM/yyyy HH:mm') as thoi_gian, 
               dd.trang_thai, 
               lh.ten_lop 
        FROM diem_danh dd
        LEFT JOIN lop_hoc lh ON dd.lop_id = lh.id
        WHERE dd.sinh_vien_id = %s
        ORDER BY dd.thoi_gian DESC
    """, (sv['id'],))
    
    # Lấy tổng số lần điểm danh
    stats_query = execute_one("""
        SELECT COUNT(*) as total_attendance,
               SUM(CASE WHEN trang_thai = 'Co mat' THEN 1 ELSE 0 END) as total_present
        FROM diem_danh
        WHERE sinh_vien_id = %s
    """, (sv['id'],))
    
    total_attendance = stats_query['total_attendance'] if stats_query and stats_query['total_attendance'] else 0
    total_present = stats_query['total_present'] if stats_query and stats_query['total_present'] else 0
    
    # Lấy lịch sử yêu cầu hỗ trợ
    support_history = execute_query("""
        SELECT TOP 5 id, tieu_de, FORMAT(thoi_gian, 'dd/MM/yyyy HH:mm') as thoi_gian, trang_thai
        FROM yeu_cau_ho_tro
        WHERE mssv = %s
        ORDER BY thoi_gian DESC
    """, (mssv,))
    
    # Xử lý Avatar và Face Data (quét thư mục)
    avatar_path = sv.get("avatar")
    face_images = []
    
    db_path = os.path.join(Config.DATABASE_DIR, mssv)
    if os.path.exists(db_path):
        images = glob.glob(f"{db_path}/*.jpg") + glob.glob(f"{db_path}/*.png")
        for img in images:
            # Đường dẫn tương đối cho frontend
            rel_path = f"database/{mssv}/{os.path.basename(img)}"
            face_images.append(rel_path)
            
    if not avatar_path or not os.path.exists(os.path.join(Config.BASE_DIR, str(avatar_path))):
        if face_images:
            avatar_path = face_images[0]
        else:
            avatar_path = None
            
    # Format lại ngày sinh
    ngay_sinh_str = ""
    if sv.get("ngay_sinh"):
        try:
            ngay_sinh_str = sv["ngay_sinh"].strftime("%d/%m/%Y")
        except:
            ngay_sinh_str = str(sv["ngay_sinh"])
            
    return jsonify({
        "success": True,
        "student": {
            "mssv": mssv,
            "ho_ten": sv["ho_ten"],
            "ten_lop": sv["ten_lop"] or "Chưa phân lớp",
            "email": sv.get("email") or "Chưa cập nhật",
            "sdt": sv.get("sdt") or "Chưa cập nhật",
            "ngay_sinh": ngay_sinh_str or "Chưa cập nhật",
            "gioi_tinh": "Nam" if sv.get("gioi_tinh") == 1 else ("Nữ" if sv.get("gioi_tinh") == 0 else "Chưa cập nhật"),
            "avatar": avatar_path
        },
        "stats": {
            "total": total_attendance,
            "present": int(total_present)
        },
        "face_data": face_images,
        "history": history,
        "support_history": support_history
    })


# ================================================================
# TRANG TỰ ĐIỂM DANH BẰNG WEBCAM (Dành cho Sinh Viên)
# ================================================================

@public_bp.route('/selfcheck')
def selfcheck():
    """
    Trang sinh viên tự điểm danh bằng webcam.
    ---
    tags:
      - Kiosk Public API
    responses:
      200:
        description: Thành công
    """
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
        
    # --- KIỂM TRA LIVENESS (CHỐNG GIẢ MẠO BẰNG MINIFASNET) ---
    from core.anti_spoofing import get_anti_spoofing
    fas_model = get_anti_spoofing()
    is_real, spoof_score, spoof_reason = fas_model.predict(frame, face['bbox'])
    
    if not is_real:
        # Lưu ảnh bằng chứng gian lận
        evidence_path = None
        try:
            import os
            import uuid
            from datetime import datetime
            from config import Config
            
            date_folder = datetime.now().strftime("%Y%m%d")
            save_dir = os.path.join(Config.EVIDENCE_DIR, 'fraud', date_folder)
            os.makedirs(save_dir, exist_ok=True)
            
            filename = f"fraud_{mssv}_{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
            abs_path = os.path.join(save_dir, filename)
            
            is_success, buffer = cv2.imencode(".jpg", frame)
            if is_success:
                buffer.tofile(abs_path)
                
            rel_path = os.path.relpath(abs_path, Config.BASE_DIR).replace('\\', '/')
            evidence_path = rel_path
        except Exception as e:
            print(f"[KIOSK] Lỗi lưu bằng chứng gian lận: {e}")

        # Ghi nhận hành vi gian lận vào bảng gian_lan_log
        from db.connection import execute_update
        sv_temp = execute_one("SELECT id FROM sinh_vien WHERE mssv = %s", (mssv,))
        if sv_temp:
            execute_update(
                "INSERT INTO gian_lan_log (sinh_vien_id, loai_gian_lan, chi_tiet, hinh_anh) VALUES (%s, %s, %s, %s)",
                (sv_temp['id'], 'Spoofing', f"Phát hiện dùng ảnh giả: {spoof_reason}. Độ trùng khớp: {sim:.2f}", evidence_path)
            )
        return {
            "success": False,
            "msg": f"Cảnh báo: Phát hiện khuôn mặt không hợp lệ ({spoof_reason}). Hành vi đã bị ghi nhận!",
            "similarity": round(sim, 2)
        }
    
    # Lấy thông tin SV
    sv = execute_one("""
        SELECT sv.mssv, sv.ho_ten, sv.email, sv.sdt, sv.avatar, sv.ngay_sinh, sv.gioi_tinh, sv.lop_id, sv.is_locked,
               lh.ten_lop, lh.ma_lop
        FROM sinh_vien sv
        LEFT JOIN lop_hoc lh ON sv.lop_id = lh.id
        WHERE sv.mssv = %s
    """, (mssv,))
    
    if not sv:
        return {"success": False, "msg": "Lỗi dữ liệu sinh viên"}
        
    if sv.get('is_locked') == 1:
        return {"success": False, "msg": "Tài khoản của bạn đã bị khóa do vi phạm quy chế. Vui lòng liên hệ Admin."}
    
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
    
    ---
    tags:
      - Kiosk Public API
    responses:
      200:
        description: Thành công
    """
    from services import attendance_service
    
    data = request.json
    if not data:
        return jsonify({"success": False, "msg": "Không có dữ liệu"})
        
    rtsp_url = data.get('rtsp_url')
    if rtsp_url:
        from core.camera import get_camera_manager
        import cv2
        import base64
        
        manager = get_camera_manager()
        cam_id = f"kiosk_{rtsp_url}"
        frame = manager.get_frame(cam_id)
        
        if frame is None:
            return jsonify({"success": False, "msg": "Không lấy được khung hình từ Camera IP"})
            
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            return jsonify({"success": False, "msg": "Lỗi xử lý ảnh"})
            
        data['image'] = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
    elif 'image' not in data:
        return jsonify({"success": False, "msg": "Không có ảnh"})
    
    lop_id = data.get('lop_id')
    start_time = data.get('start_time', 'auto')
    
    # [NEW] Kiểm tra bắt buộc chọn lớp
    if not lop_id:
        return jsonify({"success": False, "msg": "Vui lòng chọn lớp học trước khi điểm danh!"})

    if start_time == 'auto' or not start_time:
        from services.class_service import get_class_start_time
        start_time = get_class_start_time(lop_id)

    # Sử dụng hàm nhận diện chung
    recognize_result = _do_recognize(data['image'])
    
    if not recognize_result.get('success'):
        return jsonify(recognize_result)
    
    mssv = recognize_result['student']['mssv']
    sim = recognize_result['similarity']
    sv = recognize_result['student']
    
    # [NEW] Kiểm tra sinh viên có thuộc lớp được chọn không
    sv_db = execute_one("SELECT lop_id FROM sinh_vien WHERE mssv = %s", (mssv,))
    if not sv_db or str(sv_db.get('lop_id')) != str(lop_id):
        return jsonify({
            "success": False, 
            "msg": "Sinh viên không thuộc lớp này!",
            "student": sv,
            "similarity": round(sim, 2),
            "bbox": recognize_result.get('bbox'),
            "image": data['image']
        })
        
    check_lop_id = lop_id
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
        
        is_success, buffer = cv2.imencode(".jpg", frame)
        if is_success:
            buffer.tofile(abs_path)
            
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
            ghi_chu=evidence_path,
            class_start_time=start_time
        )
        if log_result and isinstance(log_result, dict):
            status_msg = "Điểm danh thành công!"
            if log_result.get('action') == 'checkin':
                status_msg = "Điểm danh vào thành công!"
                
            attendance_info = {
                'action': log_result.get('action', 'checkin'),
                'msg': status_msg
            }
    
    # Lấy lịch sử hôm nay
    today_records = execute_query("""
        SELECT FORMAT(dd.thoi_gian, 'HH:mm') as gio_vao,
               dd.trang_thai, dd.do_chinh_xac,
               lh.ten_lop
        FROM diem_danh dd
        LEFT JOIN lop_hoc lh ON dd.lop_id = lh.id
        WHERE dd.sinh_vien_id = (SELECT id FROM sinh_vien WHERE mssv = %s)
          AND CAST(dd.thoi_gian AS DATE) = CAST(GETDATE() AS DATE)
        ORDER BY dd.thoi_gian DESC
    """, (mssv,))
    
    return jsonify({
        "success": True,
        "similarity": round(sim, 2),
        "bbox": recognize_result.get('bbox'),
        "student": sv,
        "attendance": attendance_info,
        "today_records": today_records,
        "image": data['image']
    })

@public_bp.route('/api/support', methods=['POST'])
def api_support():
    """
    API nhận yêu cầu hỗ trợ từ sinh viên
    """
    data = request.json
    mssv = data.get('mssv')
    tieu_de = data.get('tieu_de')
    noi_dung = data.get('noi_dung')
    
    if not all([mssv, tieu_de, noi_dung]):
        return jsonify({"success": False, "msg": "Thiếu thông tin"})
        
    try:
        execute_update("""
            INSERT INTO yeu_cau_ho_tro (mssv, tieu_de, noi_dung)
            VALUES (%s, %s, %s)
        """, (mssv, tieu_de, noi_dung))
        return jsonify({"success": True})
    except Exception as e:
        print(f"Lỗi gửi yêu cầu hỗ trợ: {e}")
        return jsonify({"success": False, "msg": "Lỗi hệ thống"})

@public_bp.route('/api/stream_kiosk')
def stream_kiosk():
    """
    API phát luồng MJPEG từ Camera IMOU (RTSP) xuống Kiosk
    """
    from flask import Response
    from core.camera import get_camera_manager
    import cv2
    
    url = request.args.get('url')
    if not url:
        return "Missing URL", 400
        
    manager = get_camera_manager()
    cam_id = f"kiosk_{url}"
    
    if not manager.is_connected(cam_id):
        success = manager.connect(cam_id, url)
        if not success:
            return "Cannot connect to camera", 500
            
    def generate():
        import time
        while True:
            frame = manager.get_frame(cam_id)
            if frame is None:
                time.sleep(0.03)
                continue
            
            h, w = frame.shape[:2]
            if w > 640:
                scale = 640 / w
                frame = cv2.resize(frame, (640, int(h * scale)))

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ret:
                time.sleep(0.03)
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
            time.sleep(0.06) # Giới hạn ~16 FPS để tránh nhồi nhét băng thông gây lag
                   
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

