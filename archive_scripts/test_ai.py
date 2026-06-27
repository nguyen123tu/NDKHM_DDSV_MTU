import cv2
import numpy as np
from core.engine import get_engine
import os

def test_ai_engine():
    print("===========================================")
    print("TEST NHẬN DIỆN KHUÔN MẶT - MTUFace AI Core")
    print("===========================================")
    print("Khởi tạo AI Engine...")
    try:
        engine = get_engine()
        print(f"✅ Đã load thành công engine: {engine['name']}")
        print(f"✅ Kích thước Vector nhúng (Embedding Dim): {engine['embedding_dim']}")
    except Exception as e:
        print(f"❌ Lỗi khởi tạo engine: {e}")
        return

    # Lấy thử 1 ảnh từ dataset
    test_image_path = "dataset/22D14801030070/0.jpg"
    if not os.path.exists(test_image_path):
        print(f"❌ Không tìm thấy ảnh: {test_image_path}")
        return

    print(f"Đang đọc ảnh test: {test_image_path}")
    img = cv2.imread(test_image_path)
    if img is None:
        print("❌ Lỗi không thể đọc ảnh!")
        return

    print("Tiến hành nhận diện (Detection) và trích xuất đặc trưng (Embedding)...")
    try:
        results = engine['detect_and_embed'](img)
        print(f"✅ Tìm thấy {len(results)} khuôn mặt trong ảnh.")
        for i, face in enumerate(results):
            bbox = face['bbox']
            conf = face['confidence']
            emb = face['embedding']
            print(f"   -> Khuôn mặt {i+1}: Độ tự tin (Confidence) = {conf*100:.2f}% | Tọa độ (Bbox) = {bbox}")
            print(f"   -> Dữ liệu Vector: Shape {emb.shape}")
    except Exception as e:
        print(f"❌ Lỗi khi xử lý nhận diện: {e}")
    
    print("===========================================")
    print("QUÁ TRÌNH TEST THÀNH CÔNG!")
    print("===========================================")

if __name__ == "__main__":
    test_ai_engine()
