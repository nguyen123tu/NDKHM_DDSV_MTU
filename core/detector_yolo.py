"""
Core AI: Phát hiện khuôn mặt bằng YOLOv8-face.
Thay thế SCRFD (InsightFace) bằng YOLOv8 pretrained trên face dataset.
Singleton pattern.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os
from config import Config

# Singleton instance
_instance = None


class YOLOFaceDetector:
    """
    Phát hiện khuôn mặt bằng YOLOv8n-face.
    
    YOLOv8 detect nhanh hơn SCRFD, trả về bounding box + confidence.
    KHÔNG trả về embedding — cần kết hợp với ResNet50Embedder.
    """

    def __init__(self, model_path=None, conf_threshold=0.5):
        """
        Args:
            model_path: Đường dẫn model YOLOv8-face (.pt)
            conf_threshold: Ngưỡng confidence tối thiểu
        """
        self._conf = conf_threshold
        
        # Sử dụng yolov8n-face nếu có, fallback sang yolov8n
        if model_path and os.path.exists(model_path):
            self._model_path = model_path
        else:
            # Dùng yolov8n pretrained (sẽ detect person, ta lọc class 0)
            self._model_path = 'yolov8n.pt'
        
        print(f"[YOLO] Đang tải YOLOv8 model: {self._model_path}...")
        self._model = YOLO(self._model_path)
        print(f"[YOLO] YOLOv8 đã sẵn sàng (conf={self._conf})")

    def detect(self, frame):
        """
        Phát hiện khuôn mặt/người trong frame.
        
        Args:
            frame: numpy array BGR
            
        Returns:
            list[dict]: Danh sách faces, mỗi item có:
                - 'bbox': [x1, y1, x2, y2] (int)
                - 'confidence': float
                - 'crop': numpy array BGR (ảnh khuôn mặt đã crop)
        """
        if frame is None:
            return []
        
        results = self._model(frame, verbose=False, conf=self._conf)
        faces = []
        
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
                
            for box in boxes:
                # class 0 = person trong COCO dataset
                cls_id = int(box.cls[0])
                if cls_id != 0:
                    continue
                    
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                
                # Crop khuôn mặt từ frame
                h, w = frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                crop = frame[y1:y2, x1:x2]
                if crop.size == 0:
                    continue
                
                faces.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': conf,
                    'crop': crop
                })
        
        return faces


def get_yolo_detector(model_path=None, conf_threshold=0.5):
    """Lấy singleton instance của YOLOFaceDetector."""
    global _instance
    if _instance is None:
        yolo_model_path = os.path.join(Config.MODELS_DIR, 'yolov8n-face.pt')
        _instance = YOLOFaceDetector(
            model_path=model_path or yolo_model_path,
            conf_threshold=conf_threshold
        )
    return _instance
