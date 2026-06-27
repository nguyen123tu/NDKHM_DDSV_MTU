import os
import requests

def download_file(url, save_path):
    print(f"--- Đang tải: {os.path.basename(save_path)} ---")
    try:
        response = requests.get(url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Đã tải xong: {save_path}")
        else:
            print(f"❌ Lỗi tải file: {response.status_code}")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")

def main():
    # 1. Tạo thư mục
    os.makedirs('mobile_flutter/assets', exist_ok=True)
    os.makedirs('models', exist_ok=True)

    # 2. Định nghĩa URLs
    # Link MobileFaceNet TFLite (512-dim)
    TFLITE_URL = "https://github.com/shubham0204/FaceRecognition_Android/raw/master/app/src/main/assets/mobilefacenet.tflite"
    
    # Chúng ta sẽ dùng buffalo_sc của InsightFace cho Server, 
    # nên không cần tải thêm ONNX nếu bạn đã cài insightface.
    # Nhưng nếu bạn muốn chạy độc lập, link ONNX ở đây:
    # ONNX_URL = "https://github.com/onnx/models/raw/main/validated/vision/body_analysis/arcface/model/arcface-resnet100.onnx"

    print("🚀 Bắt đầu chuẩn bị bộ não Offline cho MTUFace...")
    
    # Tải file cho Flutter
    download_file(TFLITE_URL, 'mobile_flutter/assets/face_model.tflite')
    
    print("\n" + "="*50)
    print("HOÀN TẤT!")
    print("1. Hãy mở file .env và sửa: AI_ENGINE=buffalo_sc")
    print("2. Chạy lại Server: python app.py")
    print("3. Trong mobile_flutter, chạy: flutter pub get")
    print("="*50)

if __name__ == "__main__":
    main()
