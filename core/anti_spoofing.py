import os
import cv2
import numpy as np
import onnxruntime as ort
from config import Config

class AntiSpoofingModel:
    def __init__(self, model_path="models/MiniFASNetV2.onnx"):
        self.model_path = os.path.join(Config.BASE_DIR, model_path)
        self.session = None
        self.scale = 2.7
        self.input_size = (80, 80)
        
        if os.path.exists(self.model_path):
            try:
                self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
                self.input_name = self.session.get_inputs()[0].name
            except Exception as e:
                print(f"[AntiSpoofing] Lỗi load mô hình: {e}")
        else:
            print(f"[AntiSpoofing] Cảnh báo: Không tìm thấy {self.model_path}")

    def _xyxy2xywh(self, bbox: list) -> list:
        x1, y1, x2, y2 = bbox
        return [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]

    def _crop_face(self, image: np.ndarray, bbox: list) -> np.ndarray:
        """Crop and resize face region from image."""
        src_h, src_w = image.shape[:2]
        x, y, box_w, box_h = bbox

        scale = min((src_h - 1) / box_h, (src_w - 1) / box_w, self.scale)
        new_w = box_w * scale
        new_h = box_h * scale

        center_x = x + box_w / 2
        center_y = y + box_h / 2

        x1 = max(0, int(center_x - new_w / 2))
        y1 = max(0, int(center_y - new_h / 2))
        x2 = min(src_w - 1, int(center_x + new_w / 2))
        y2 = min(src_h - 1, int(center_y + new_h / 2))

        cropped = image[y1 : y2 + 1, x1 : x2 + 1]
        return cv2.resize(cropped, self.input_size[::-1])

    def _preprocess(self, image: np.ndarray, bbox: list) -> np.ndarray:
        face = self._crop_face(image, bbox)
        face = face.astype(np.float32)
        face = np.transpose(face, (2, 0, 1))
        face = np.expand_dims(face, axis=0)
        return face

    def predict(self, image, bbox_xyxy):
        if self.session is None:
            return True, 1.0, "Không có mô hình"
            
        bbox_xywh = self._xyxy2xywh(bbox_xyxy)
        input_tensor = self._preprocess(image, bbox_xywh)
        
        outputs = self.session.run(None, {self.input_name: input_tensor})
        logits = outputs[0]
        
        e_x = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = e_x / e_x.sum(axis=1, keepdims=True)
        
        label_idx = int(np.argmax(probs))
        score = float(probs[0, label_idx])
        
        # label_idx: 1 là Real, 0/2 là Fake
        if label_idx == 1 and score > 0.6:
            return True, score, "Người thật"
        else:
            reason = "Màn hình/Điện thoại" if label_idx == 2 else "Ảnh in/Giấy"
            return False, score, f"Phát hiện giả mạo ({reason})"

_anti_spoofing_instance = None
def get_anti_spoofing():
    global _anti_spoofing_instance
    if _anti_spoofing_instance is None:
        _anti_spoofing_instance = AntiSpoofingModel()
    return _anti_spoofing_instance
