"""
Route Training AI
"""

from flask import render_template, request, jsonify, Response
import threading
import json
import os
import cv2

from . import training_bp
from utils.decorators import login_required
from core.trainer import FaceTrainer
from config import Config
from services import student_service

# Global trainer
_trainer = FaceTrainer()
_training_thread = None

@training_bp.route('/')
@login_required
def index():
    # Lấy danh sách SV có thông tin số lượng ảnh và da_train
    students = student_service.get_all(per_page=1000)['items']
    
    # Tính toán lại số lượng ảnh cho chuẩn
    for sv in students:
        sv['image_count'] = student_service.count_images(sv['mssv'])
    
    # Kiểm tra trạng thái pkl files
    insightface_ready = os.path.exists(Config.EMBEDDINGS_PATH)
    yolo_ready = os.path.exists(Config.EMBEDDINGS_YOLO_PATH)
        
    return render_template('training/index.html', 
                          students=students,
                          current_engine=Config.AI_ENGINE,
                          insightface_ready=insightface_ready,
                          yolo_ready=yolo_ready)


@training_bp.route('/switch-engine', methods=['POST'])
@login_required
def switch_engine():
    """Chuyển đổi AI Engine giữa InsightFace và YOLOv8+ResNet50."""
    data = request.json
    new_engine = data.get('engine', 'insightface')
    
    if new_engine not in ('insightface', 'yolo_resnet'):
        return jsonify({"success": False, "msg": "Engine không hợp lệ"}), 400
    
    # Cập nhật Config runtime
    Config.AI_ENGINE = new_engine
    
    # Reset matcher singleton để nó load file pkl mới
    from core import matcher as matcher_module
    matcher_module._instance = None
    
    # Reset engine cache trong trainer
    global _trainer
    _trainer = FaceTrainer()
    
    engine_name = "InsightFace (ArcFace + SCRFD)" if new_engine == 'insightface' else "YOLOv8 + ResNet50"
    print(f"[ENGINE SWITCH] Đã chuyển sang: {engine_name}")
    
    return jsonify({
        "success": True, 
        "engine": new_engine,
        "engine_name": engine_name
    })

@training_bp.route('/start', methods=['POST'])
@login_required
def start():
    global _training_thread
    
    if _training_thread and _training_thread.is_alive():
        return jsonify({"success": False, "msg": "Đang trong quá trình training!"}), 400
        
    def run_train():
        _trainer.train_all()
        # Cập nhật toàn bộ sinh viên thành trạng thái da_train = 1
        students = student_service.get_all(per_page=10000)['items']
        for sv in students:
            if student_service.count_images(sv['mssv']) > 0:
                student_service.mark_trained(sv['mssv'])
                
    _training_thread = threading.Thread(target=run_train)
    _training_thread.start()
    
    return jsonify({"success": True})

@training_bp.route('/progress')
@login_required
def progress():
    """SSE endpoint để stream tiến độ về client"""
    def generate():
        while True:
            import time
            time.sleep(0.5)
            status = _trainer.get_progress()
            yield f"data: {json.dumps(status)}\n\n"
            if status['status'] in ['done', 'error']:
                break
    return Response(generate(), mimetype='text/event-stream')

@training_bp.route('/student/<mssv>', methods=['POST'])
@login_required
def train_single(mssv):
    success = _trainer.train_one(mssv)
    if success:
        student_service.mark_trained(mssv)
        return jsonify({"success": True})
    return jsonify({"success": False, "msg": "Không đủ dữ liệu ảnh"}), 400

@training_bp.route('/capture/<mssv>', methods=['GET', 'POST'])
@login_required
def capture(mssv):
    # Form GET trả về page chụp ảnh AJAX
    if request.method == 'GET':
        sv = student_service.get_by_mssv(mssv)
        if not sv:
            return "Not found", 404
        return render_template('training/capture.html', student=sv)
        
    # Xử lý upload frame AJAX (Base64)
    # Đây là logic chụp đơn giản, client gửi base64 lên
    import base64
    import numpy as np
    
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"success": False}), 400
        
    img_data = data['image'].split(',')[1]
    img_bytes = base64.b64decode(img_data)
    img_np = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    
    # Lưu vào database/MSSV/
    student_dir = os.path.join(Config.DATABASE_DIR, mssv)
    os.makedirs(student_dir, exist_ok=True)
    
    idx = data.get('index', 0)
    file_path = os.path.join(student_dir, f"{idx}.jpg")
    
    # Fix cho OpenCV ghi file tiếng Việt trên Windows
    is_success, buffer = cv2.imencode(".jpg", frame)
    if is_success:
        buffer.tofile(file_path)
    
    return jsonify({"success": True})
