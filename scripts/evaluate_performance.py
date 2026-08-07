import os
import sys
import time
import cv2
import numpy as np

# Thêm đường dẫn gốc vào sys.path để import các module core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import Config
from core.engine import get_engine

def evaluate_engine(engine_name, duration=60):
    """
    Đánh giá hiệu năng (FPS) của AI Engine trong một khoảng thời gian.
    
    Args:
        engine_name: Tên engine ('insightface', 'yolo_resnet', etc.)
        duration: Thời gian chạy (giây)
    """
    print(f"\n{'='*50}")
    print(f"BẮT ĐẦU ĐÁNH GIÁ HIỆU NĂNG: {engine_name.upper()}")
    print(f"Thời gian thử nghiệm: {duration} giây")
    print(f"{'='*50}")

    # Tạm thời đổi config engine để tải đúng engine
    original_engine = Config.AI_ENGINE
    Config.AI_ENGINE = engine_name
    
    # 1. Tải Engine
    print("[1] Đang tải AI Engine...")
    start_load = time.time()
    engine = get_engine()
    print(f"[1] Tải xong sau {time.time() - start_load:.2f}s")
    
    # 2. Khởi tạo Camera (sử dụng camera mặc định 0)
    print("[2] Khởi tạo Camera (ID 0)...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("LỖI: Không thể mở camera.")
        return
        
    print(f"[2] Camera sẵn sàng. Bắt đầu đo FPS trong {duration} giây...")
    print("Vui lòng đứng trước camera và có các cử động bình thường.")
    
    fps_list = []
    start_time = time.time()
    frames_in_second = 0
    second_start = time.time()
    
    try:
        while (time.time() - start_time) < duration:
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Resize để test công bằng (như code thực tế)
            h, w = frame.shape[:2]
            if w > 1280:
                scale = 1280 / w
                frame = cv2.resize(frame, (1280, int(h * scale)))
                
            # Đo thời gian xử lý AI
            t1 = time.time()
            faces = engine["detect_and_embed"](frame)
            t2 = time.time()
            
            # Tính FPS khung hình này và cộng dồn
            frames_in_second += 1
            if time.time() - second_start >= 1.0:
                current_fps = frames_in_second
                fps_list.append(current_fps)
                print(f"[{int(time.time() - start_time)}s] FPS: {current_fps} | Số khuôn mặt: {len(faces)}")
                
                frames_in_second = 0
                second_start = time.time()
                
            # Hiển thị
            cv2.putText(frame, f"Testing {engine_name}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Evaluation", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Đã hủy bởi người dùng.")
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        Config.AI_ENGINE = original_engine
        
    # 3. Tính toán và Báo cáo
    if len(fps_list) > 0:
        avg_fps = np.mean(fps_list)
        max_fps = np.max(fps_list)
        min_fps = np.min(fps_list)
        
        print(f"\n{'='*50}")
        print(f"KẾT QUẢ ĐÁNH GIÁ: {engine_name.upper()}")
        print(f"{'='*50}")
        print(f"Camera: Webcam mặc định")
        print(f"Thời gian test: {len(fps_list)} giây")
        print(f"Trung bình (Avg FPS): {avg_fps:.2f}")
        print(f"Nhỏ nhất (Min FPS) : {min_fps}")
        print(f"Lớn nhất (Max FPS) : {max_fps}")
        print(f"{'='*50}")
        
        # Ghi log ra file
        log_file = os.path.join(os.path.dirname(__file__), f"performance_{engine_name}.txt")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')} - {engine_name.upper()}\n")
            f.write(f"Camera: Webcam mặc định\n")
            f.write(f"Thời gian test: {len(fps_list)} giây\n")
            f.write(f"Avg FPS: {avg_fps:.2f}\n")
            f.write(f"Min FPS: {min_fps}\n")
            f.write(f"Max FPS: {max_fps}\n")
            f.write("-" * 40 + "\n")
            
        print(f"Đã lưu kết quả vào {log_file}")
    else:
        print("Không thu thập được đủ dữ liệu.")

if __name__ == "__main__":
    # Bạn có thể thay đổi thời gian chạy ở đây (mặc định 60 giây)
    test_duration = 60 
    
    print("Chọn AI Engine để test:")
    print("1. InsightFace")
    print("2. YOLO11 + ResNet50")
    choice = input("Nhập số (1 hoặc 2): ")
    
    if choice == '1':
        evaluate_engine("insightface", test_duration)
    elif choice == '2':
        evaluate_engine("yolo_resnet", test_duration)
    else:
        print("Lựa chọn không hợp lệ.")
