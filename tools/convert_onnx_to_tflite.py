"""
Script hỗ trợ chuyển đổi mô hình ONNX của InsightFace sang TFLite cho ứng dụng Flutter.
Yêu cầu cài đặt: 
pip install tensorflow onnx onnx-tf
"""
import os
import onnx
from onnx_tf.backend import prepare
import tensorflow as tf

def convert_to_tflite():
    # Đường dẫn tới file model ONNX của InsightFace (Mặc định khi tải về)
    user_home = os.path.expanduser('~')
    onnx_model_path = os.path.join(user_home, '.insightface', 'models', 'buffalo_l', 'w600k_r50.onnx')
    
    if not os.path.exists(onnx_model_path):
        print(f"❌ Không tìm thấy file ONNX tại: {onnx_model_path}")
        print("Vui lòng đảm bảo bạn đang dùng InsightFace và đã chạy file app.py ít nhất 1 lần để hệ thống tải model buffalo_l về máy.")
        return

    tf_model_path = "w600k_r50_tf_saved_model"
    tflite_model_path = "face_model.tflite"

    try:
        print(f"⏳ Bước 1: Đọc mô hình ONNX từ {onnx_model_path}...")
        onnx_model = onnx.load(onnx_model_path)

        print("⏳ Bước 2: Chuyển đổi từ ONNX sang TensorFlow (Có thể tốn vài phút và ngốn RAM)...")
        tf_rep = prepare(onnx_model)
        tf_rep.export_graph(tf_model_path)

        print("⏳ Bước 3: Chuyển đổi từ TensorFlow sang TFLite...")
        converter = tf.lite.TFLiteConverter.from_saved_model(tf_model_path)
        
        # Optimize cho kích thước (Nén file từ ~90MB xuống còn khoảng 20-30MB)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        tflite_model = converter.convert()

        print("⏳ Bước 4: Lưu file face_model.tflite...")
        with open(tflite_model_path, 'wb') as f:
            f.write(tflite_model)
            
        print(f"✅ HOÀN TẤT! File đã được lưu tại: {os.path.abspath(tflite_model_path)}")
        print(f"👉 Bây giờ hãy copy file này vào thư mục: mobile_flutter/assets/")
        
    except Exception as e:
        print(f"❌ Xảy ra lỗi trong quá trình convert: {e}")
        print("Gợi ý: Quá trình này đòi hỏi máy có RAM tốt. Đảm bảo bạn đã cài đủ các thư viện.")

if __name__ == "__main__":
    convert_to_tflite()
