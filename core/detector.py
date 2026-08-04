"""
Core AI: Phát hiện khuôn mặt bằng SCRFD (InsightFace).
Singleton pattern — chỉ load model 1 lần duy nhất trong toàn bộ ứng dụng.
"""

import cv2
import numpy as np
from insightface.app import FaceAnalysis

# Singleton instance
_instance = None


class FaceDetector:
    """
    Phát hiện khuôn mặt trong frame ảnh bằng InsightFace SCRFD.

    Sử dụng CPUExecutionProvider để chạy trên mọi máy tính.
    Singleton pattern để không load model lặp lại nhiều lần.
    """

    def __init__(self, det_size=(640, 640)):
        """
        Khởi tạo InsightFace FaceAnalysis.

        Args:
            det_size: Kích thước ảnh đầu vào cho detector (width, height)
        """
        print("[AI] Đang tải InsightFace SCRFD model...")
        self._app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        self._app.prepare(ctx_id=0, det_size=det_size)
        self._det_size = det_size
        print(f"[AI] InsightFace đã sẵn sàng (det_size={det_size})")

    def detect(self, frame):
        """
        Phát hiện tất cả khuôn mặt trong frame.

        Args:
            frame: numpy array BGR từ OpenCV

        Returns:
            list: Danh sách các face objects, mỗi face có:
                  - .bbox: [x1, y1, x2, y2]
                  - .embedding: numpy array 512 chiều
                  - .kps: key points
                  - .det_score: confidence score
        """
        if frame is None:
            return []
        faces = self._app.get(frame)
        return faces

    def draw_boxes(self, frame, faces, names=None, similarities=None):
        """
        Vẽ bounding box và tên lên frame.

        Args:
            frame: numpy array BGR
            faces: list face objects từ detect()
            names: list tên tương ứng (optional)
            similarities: list điểm similarity (optional)

        Returns:
            numpy array: Frame đã được vẽ box
        """
        result = frame.copy()

        for i, face in enumerate(faces):
            x1, y1, x2, y2 = face.bbox.astype(int)

            # Xác định tên và màu
            name = names[i] if names and i < len(names) else "UNKNOWN"
            sim = similarities[i] if similarities and i < len(similarities) else 0.0

            if name == "UNKNOWN":
                color = (0, 0, 255)  # Đỏ — Kẻ lạ
                label = "Ke La (Canh Bao)"
            else:
                color = (0, 255, 0)  # Xanh lá — Đã nhận diện
                label = f"{name} ({sim:.0%})"

            # Vẽ box và label
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)

            # Tính kích thước text để vẽ nền
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_w, text_h), _ = cv2.getTextSize(label, font, font_scale, thickness)

            # Vẽ nền cho text
            cv2.rectangle(
                result, (x1, y1 - text_h - 10), (x1 + text_w + 5, y1), color, -1
            )
            cv2.putText(
                result,
                label,
                (x1 + 2, y1 - 5),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
            )

        return result


def get_detector(det_size=(640, 640)):
    """
    Lấy singleton instance của FaceDetector.
    Đảm bảo model chỉ được load 1 lần duy nhất.
    """
    global _instance
    if _instance is None:
        _instance = FaceDetector(det_size=det_size)
    return _instance


if __name__ == "__main__":
    # Test: Mở webcam và phát hiện khuôn mặt
    print("=== TEST FACE DETECTOR ===")
    detector = get_detector()
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        faces = detector.detect(frame)
        frame = detector.draw_boxes(frame, faces)

        cv2.putText(
            frame,
            f"Faces: {len(faces)}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )
        cv2.imshow("Face Detector Test", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
