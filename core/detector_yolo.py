"""
Core AI: Phát hiện khuôn mặt bằng YOLO11-face.
Thay thế SCRFD (InsightFace) bằng YOLO11 pretrained trên face dataset.
Singleton pattern.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os
import torch
from config import Config

# Singleton instance
_instance = None


class YOLOFaceDetector:
    """
    Phát hiện khuôn mặt bằng YOLO11.

    YOLO11 cung cấp độ chính xác cao hơn và tốc độ nhanh hơn (FPS cao hơn).
    Model nên được train trên face dataset (VD: yolo11n-face.pt).
    """

    def __init__(self, model_path=None, conf_threshold=0.5):
        self._conf = conf_threshold

        # Ưu tiên sử dụng mô hình YOLO11 (yolo11n-face.pt cho khuôn mặt)
        priority_models = [
            model_path,
            os.path.join(Config.MODELS_DIR, "yolo11n-face.pt"),
            "yolo11n.pt",  # Tự động tải nếu không có file local
        ]

        selected_model = "yolo11n.pt"
        for m in priority_models:
            if m and (
                os.path.exists(m) or not m.endswith(".pt")
            ):  # .pt check cho file local
                selected_model = m
                break

        print(f"[YOLO] Đang khởi tạo model YOLO11: {selected_model}...")
        self._model = YOLO(selected_model)
        self._model_name = selected_model

        # Tối ưu hóa Inference: Sử dụng GPU FP16 (half precision) nếu có CUDA
        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self._half = True if self._device == "cuda:0" else False
        print(f"[YOLO] Cấu hình Inference: device={self._device}, half={self._half}")

        # Khởi động trước (Warmup) để tránh lag frame đầu tiên
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
        _ = self._model(dummy_img, verbose=False, device=self._device, half=self._half)

        print(f"[YOLO] {selected_model} đã sẵn sàng (conf={self._conf})")

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

        # Thực hiện suy luận (Inference)
        results = self._model(
            frame, verbose=False, conf=self._conf, device=self._device, half=self._half
        )
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

                faces.append(
                    {"bbox": [x1, y1, x2, y2], "confidence": conf, "crop": crop}
                )

        return faces


def get_yolo_detector(model_path=None, conf_threshold=0.5):
    """Lấy singleton instance của YOLOFaceDetector."""
    global _instance
    if _instance is None:
        _instance = YOLOFaceDetector(
            model_path=model_path, conf_threshold=conf_threshold
        )
    return _instance
