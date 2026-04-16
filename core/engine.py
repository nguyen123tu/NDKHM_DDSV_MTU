"""
Core AI: Engine Factory — Chọn giữa InsightFace và YOLOv8+ResNet50.

Factory Pattern cho phép chuyển đổi AI engine mà không cần sửa code.
Cấu hình qua Config.AI_ENGINE: 'insightface' hoặc 'yolo_resnet'
"""

from config import Config


def get_engine():
    """
    Factory: Trả về cặp (detect_fn, embed_fn) tùy theo Config.AI_ENGINE.
    
    Returns:
        dict: {
            'name': str,              — Tên engine
            'detect': callable,        — Hàm detect(frame) → faces
            'embed': callable,         — Hàm embed(face_crop) → vector
            'detect_and_embed': callable — Hàm detect+embed(frame) → [(bbox, embedding), ...]
        }
    """
    engine_name = getattr(Config, 'AI_ENGINE', 'insightface')
    
    if engine_name == 'yolo_resnet':
        return _build_yolo_resnet_engine()
    else:
        return _build_insightface_engine()


def _build_insightface_engine():
    """
    Engine InsightFace (buffalo_l).
    Tích hợp sẵn: SCRFD detect + ArcFace embed trong 1 lần gọi.
    """
    from insightface.app import FaceAnalysis
    
    print("[ENGINE] Đang khởi tạo InsightFace engine...")
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=Config.DET_SIZE)
    print("[ENGINE] InsightFace engine đã sẵn sàng.")
    
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
