"""
API Routes cho DeepFace — Xác thực khuôn mặt, phân tích, anti-spoofing.

Các endpoint:
  POST /api/deepface/verify     — So sánh 2 ảnh khuôn mặt
  POST /api/deepface/analyze    — Phân tích thuộc tính (tuổi, giới tính, cảm xúc)
  POST /api/deepface/liveness   — Kiểm tra khuôn mặt thật/giả
  GET  /api/deepface/models     — Danh sách model hỗ trợ
  GET  /api/deepface/status     — Trạng thái engine hiện tại
"""

import base64
import numpy as np
import cv2
from flask import Blueprint, request, jsonify
from config import Config

deepface_bp = Blueprint('deepface_api', __name__, url_prefix='/api/deepface')


def _decode_base64_image(base64_str):
    """Decode base64 string thành numpy array BGR."""
    try:
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


@deepface_bp.route('/verify', methods=['POST'])
def verify_faces():
    """
    So sánh 2 ảnh khuôn mặt (dùng cho mobile check-in).
    
    Body JSON:
        img1: base64 encoded image 1
        img2: base64 encoded image 2
        
    Returns:
        {
            "verified": bool,
            "distance": float,
            "threshold": float,
            "confidence": float,
            "model": str
        }
    """
    if Config.AI_ENGINE != 'deepface':
        return jsonify({
            'success': False,
            'msg': 'DeepFace engine chưa được kích hoạt. Đặt AI_ENGINE=deepface trong .env'
        }), 400

    data = request.json
    img1_b64 = data.get('img1', '')
    img2_b64 = data.get('img2', '')

    if not img1_b64 or not img2_b64:
        return jsonify({'success': False, 'msg': 'Cần cung cấp 2 ảnh (img1, img2)'}), 400

    img1 = _decode_base64_image(img1_b64)
    img2 = _decode_base64_image(img2_b64)

    if img1 is None or img2 is None:
        return jsonify({'success': False, 'msg': 'Không decode được ảnh'}), 400

    from core.engine import get_engine
    engine = get_engine()

    if 'verify_two_faces' not in engine:
        return jsonify({'success': False, 'msg': 'Engine hiện tại không hỗ trợ verify'}), 400

    result = engine['verify_two_faces'](img1, img2)
    result['success'] = True
    return jsonify(result)


@deepface_bp.route('/analyze', methods=['POST'])
def analyze_face():
    """
    Phân tích thuộc tính khuôn mặt.
    
    Body JSON:
        image: base64 encoded image
        actions: list of actions (optional, default: ["age", "gender", "emotion"])
        
    Returns:
        list[{
            "bbox": [x1, y1, x2, y2],
            "age": float,
            "gender": str,
            "dominant_emotion": str,
            ...
        }]
    """
    if Config.AI_ENGINE != 'deepface':
        return jsonify({
            'success': False,
            'msg': 'DeepFace engine chưa được kích hoạt'
        }), 400

    data = request.json
    img_b64 = data.get('image', '')
    actions = data.get('actions', ['age', 'gender', 'emotion'])

    if not img_b64:
        return jsonify({'success': False, 'msg': 'Cần cung cấp ảnh (image)'}), 400

    img = _decode_base64_image(img_b64)
    if img is None:
        return jsonify({'success': False, 'msg': 'Không decode được ảnh'}), 400

    from core.engine import get_engine
    engine = get_engine()

    if 'analyze_face' not in engine:
        return jsonify({'success': False, 'msg': 'Engine hiện tại không hỗ trợ analyze'}), 400

    results = engine['analyze_face'](img, actions=tuple(actions))
    return jsonify({'success': True, 'faces': results})


@deepface_bp.route('/liveness', methods=['POST'])
def check_liveness():
    """
    Kiểm tra khuôn mặt thật hay giả (anti-spoofing).
    
    Body JSON:
        image: base64 encoded image
        
    Returns:
        list[{
            "bbox": [x1, y1, x2, y2],
            "is_real": bool,
            "antispoof_score": float,
            "confidence": float
        }]
    """
    if Config.AI_ENGINE != 'deepface':
        return jsonify({
            'success': False,
            'msg': 'DeepFace engine chưa được kích hoạt'
        }), 400

    data = request.json
    img_b64 = data.get('image', '')

    if not img_b64:
        return jsonify({'success': False, 'msg': 'Cần cung cấp ảnh (image)'}), 400

    img = _decode_base64_image(img_b64)
    if img is None:
        return jsonify({'success': False, 'msg': 'Không decode được ảnh'}), 400

    from core.engine import get_engine
    engine = get_engine()

    if 'verify_liveness' not in engine:
        return jsonify({'success': False, 'msg': 'Engine hiện tại không hỗ trợ liveness'}), 400

    results = engine['verify_liveness'](img)
    return jsonify({'success': True, 'faces': results})


@deepface_bp.route('/models', methods=['GET'])
def list_models():
    """Trả về danh sách model DeepFace hỗ trợ."""
    from core.engine_deepface import MODEL_DIMS

    models = []
    for name, dim in MODEL_DIMS.items():
        models.append({
            'name': name,
            'embedding_dim': dim,
            'is_active': (Config.AI_ENGINE == 'deepface' and 
                         getattr(Config, 'DEEPFACE_MODEL', 'ArcFace') == name)
        })

    detectors = [
        {'name': 'opencv', 'desc': 'OpenCV Haar Cascade — Nhanh, nhẹ'},
        {'name': 'retinaface', 'desc': 'RetinaFace — Chính xác cao'},
        {'name': 'mtcnn', 'desc': 'MTCNN — Cân bằng tốc độ/chính xác'},
        {'name': 'ssd', 'desc': 'SSD — Nhanh, GPU-friendly'},
        {'name': 'dlib', 'desc': 'Dlib HOG — Cổ điển, ổn định'},
        {'name': 'mediapipe', 'desc': 'MediaPipe — Google, nhẹ'},
        {'name': 'yolov8n', 'desc': 'YOLOv8 Nano — Realtime'},
        {'name': 'yolov11n', 'desc': 'YOLOv11 Nano — SOTA'},
        {'name': 'centerface', 'desc': 'CenterFace — Nhẹ, nhanh'},
        {'name': 'yunet', 'desc': 'YuNet — OpenCV DNN'},
    ]

    return jsonify({
        'success': True,
        'recognition_models': models,
        'detectors': detectors,
        'current_engine': Config.AI_ENGINE,
        'current_model': getattr(Config, 'DEEPFACE_MODEL', 'N/A'),
        'current_detector': getattr(Config, 'DEEPFACE_DETECTOR', 'N/A'),
    })


@deepface_bp.route('/status', methods=['GET'])
def engine_status():
    """Trả về trạng thái engine hiện tại."""
    status = {
        'engine': Config.AI_ENGINE,
        'deepface_enabled': Config.AI_ENGINE == 'deepface',
    }

    if Config.AI_ENGINE == 'deepface':
        status.update({
            'model': getattr(Config, 'DEEPFACE_MODEL', 'ArcFace'),
            'detector': getattr(Config, 'DEEPFACE_DETECTOR', 'retinaface'),
            'anti_spoofing': getattr(Config, 'DEEPFACE_ANTI_SPOOFING', False),
            'analysis_actions': getattr(Config, 'DEEPFACE_ANALYSIS_ACTIONS', ''),
        })

    return jsonify({'success': True, **status})
