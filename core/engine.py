"""
Core AI: Engine Factory — Chọn giữa InsightFace, YOLOv8+ResNet50, và DeepFace.

Factory Pattern cho phép chuyển đổi AI engine mà không cần sửa code.
Cấu hình qua Config.AI_ENGINE:
  - 'insightface'   — InsightFace buffalo_l (mặc định)
  - 'buffalo_sc'    — InsightFace buffalo_sc (nhẹ, nhanh)
  - 'yolo_resnet'   — YOLOv8 + ResNet50
  - 'deepface'      — DeepFace (đa model: ArcFace, Facenet512, GhostFaceNet, ...)
"""

from config import Config


def get_engine():
    """
    Factory: Trả về engine dict tùy theo Config.AI_ENGINE.
    
    Returns:
        dict: {
            'name': str,              — Tên engine
            'embedding_dim': int,      — Số chiều embedding vector
            'detect_and_embed': callable — Hàm detect+embed(frame) → [{bbox, embedding, confidence}, ...]
            
            # Chỉ có khi dùng DeepFace:
            'analyze_face': callable,      — Phân tích thuộc tính (tuổi, giới tính, cảm xúc)
            'verify_liveness': callable,   — Kiểm tra khuôn mặt thật/giả (anti-spoofing)
            'verify_two_faces': callable,  — So sánh 2 ảnh khuôn mặt
        }
    """
    engine_name = getattr(Config, 'AI_ENGINE', 'insightface')
    
    if engine_name == 'deepface':
        return _build_deepface_engine()
    elif engine_name == 'yolo_resnet':
        return _build_yolo_resnet_engine()
    elif engine_name == 'buffalo_sc':
        return _build_insightface_engine(model_name='buffalo_sc')
    else:
        return _build_insightface_engine(model_name='buffalo_l')


def _build_deepface_engine():
    """
    Engine DeepFace — Hỗ trợ đa dạng model và detector.
    
    Cấu hình qua Config:
      - DEEPFACE_MODEL: Tên model nhận diện (mặc định: ArcFace)
      - DEEPFACE_DETECTOR: Tên detector (mặc định: retinaface)
      - DEEPFACE_ANTI_SPOOFING: Bật anti-spoofing (mặc định: False)
    """
    from core.engine_deepface import build_deepface_engine
    
    model_name = getattr(Config, 'DEEPFACE_MODEL', 'ArcFace')
    detector = getattr(Config, 'DEEPFACE_DETECTOR', 'retinaface')
    anti_spoofing = getattr(Config, 'DEEPFACE_ANTI_SPOOFING', False)
    
    return build_deepface_engine(
        model_name=model_name,
        detector_backend=detector,
        anti_spoofing=anti_spoofing,
    )


def _build_insightface_engine(model_name='buffalo_l'):
    """
    Engine InsightFace.
    buffalo_l: Toàn diện, chính xác cao (90MB).
    buffalo_sc: Siêu nhẹ, MobileFaceNet (1MB), phù hợp đồng bộ mobile.
    """
    from insightface.app import FaceAnalysis
    
    print(f"[ENGINE] Đang khởi tạo InsightFace ({model_name})...")
    app = FaceAnalysis(name=model_name, providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=Config.DET_SIZE)
    print(f"[ENGINE] {model_name} đã sẵn sàng.")
    
    def detect_and_embed(frame):
        """
        InsightFace detect + embed trong 1 bước.
        
        Returns:
            list[dict]: [{
                'bbox': [x1,y1,x2,y2],
                'embedding': numpy array 512d,
                'confidence': float
            }, ...]
        """
        if frame is None:
            return []
        
        faces = app.get(frame)
        results = []
        for face in faces:
            import numpy as np
            emb = face.embedding
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            
            results.append({
                'bbox': face.bbox.astype(int).tolist(),
                'embedding': emb,
                'confidence': float(face.det_score)
            })
        return results
    
    return {
        'name': 'InsightFace (ArcFace + SCRFD)',
        'embedding_dim': 512,
        'detect_and_embed': detect_and_embed
    }


def _build_yolo_resnet_engine():
    """
    Engine YOLOv8 + ResNet50.
    YOLOv8 detect → Crop face → ResNet50 embed.
    """
    from core.detector_yolo import get_yolo_detector
    from core.embedder_resnet import get_resnet_embedder
    
    print("[ENGINE] Đang khởi tạo YOLOv8 + ResNet50 engine...")
    detector = get_yolo_detector()
    embedder = get_resnet_embedder()
    print("[ENGINE] YOLOv8 + ResNet50 engine đã sẵn sàng.")
    
    def detect_and_embed(frame):
        """
        YOLOv8 detect → crop → ResNet50 embed.
        
        Returns:
            list[dict]: [{
                'bbox': [x1,y1,x2,y2],
                'embedding': numpy array 2048d,
                'confidence': float
            }, ...]
        """
        if frame is None:
            return []
        
        faces_detected = detector.detect(frame)
        results = []
        
        for face in faces_detected:
            emb = embedder.embed(face['crop'])
            if emb is not None:
                results.append({
                    'bbox': face['bbox'],
                    'embedding': emb,
                    'confidence': face['confidence']
                })
        
        return results
    
    return {
        'name': 'YOLOv8 + ResNet50',
        'embedding_dim': embedder.embedding_dim,
        'detect_and_embed': detect_and_embed
    }
