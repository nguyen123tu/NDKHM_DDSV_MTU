"""
Script đánh giá mức độ chính xác của hệ thống nhận diện khuôn mặt (System Evaluation).
Dùng để vẽ Confusion Matrix, tính Accuracy, Precision, Recall cho báo cáo tốt nghiệp.

CÁCH SỬ DỤNG:
1. Mở Terminal / CMD, cài các thư viện vẽ biểu đồ:
   pip install scikit-learn matplotlib seaborn
   
2. Tạo thư mục 'evaluation_data' ở ngang hàng với file app.py.
3. Bên trong 'evaluation_data', tạo các thư mục con mang tên MSSV của sinh viên (Ví dụ: '22d14801030074').
4. Vứt 5-10 ảnh CỦA RIÊNG SINH VIÊN ĐÓ vào trong thư mục mang tên họ.
5. Tạo 1 thư mục đặc biệt tên là 'UNKNOWN' và vứt 10-20 ảnh của NGƯỜI LẠ vào đó.
6. Chạy lệnh: python evaluate_system.py

Script sẽ quét toàn bộ ảnh, cho ngầm gọi não bộ AI InsightFace, so sánh kết quả 
với tên thư mục gốc, và cuối cùng tính ra các chỉ số % + vẽ hình vào file evaluation_results.png
"""

import os
import time
import glob
import cv2
import numpy as np

# Các thư viện toán học và vẽ (Nếu máy báo thiếu thì chạy pip install scikit-learn matplotlib seaborn)
try:
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError:
    print("Vui lòng cài đặt thêm các thư viện vẽ biểu đồ để chạy script này!")
    print("Mở terminal và gõ: pip install scikit-learn matplotlib seaborn")
    exit()

# Setup config Flask để load database mượt mà
from app import app
from config import Config
from core.engine import get_engine
from core.matcher import get_matcher
from services import student_service

EVALUATION_DIR = os.path.join(Config.BASE_DIR, 'evaluation_data')

def ensure_folders():
    if not os.path.exists(EVALUATION_DIR):
        os.makedirs(EVALUATION_DIR)
        unknown_path = os.path.join(EVALUATION_DIR, 'UNKNOWN')
        os.makedirs(unknown_path)
        print("==================================================================")
        print(f" Đã tạo thư mục test: {EVALUATION_DIR}")
        print(" Vui lòng làm theo hướng dẫn:")
        print(" 1. Copy thư mục 1 mã sinh viên (VD: '123456') chứa vài ảnh test chưa từng train vào mạng.")
        print(" 2. Copy vài ảnh của người lạ mặt vào thư mục 'UNKNOWN'.")
        print(" 3. Sau đó chạy lại thư mục này.")
        print("==================================================================")
        return False
    return True

def run_evaluation():
    print("Bắt đầu load Não (AI Model)... Vui lòng đợi...")
    
    # Context app để kết nối DB nếu cần
    with app.app_context():
        engine = get_engine()
        detect_and_embed = engine['detect_and_embed']
        
        # Load não bộ sinh viên từ database (file .npy)
        matcher = get_matcher()
        matcher.reload_if_updated()
        print(f"Đã nạp {len(matcher._known_faces)} khuôn mặt sinh viên vào não.")
        
        y_true = []
        y_pred = []
        
        # Lấy tất cả ảnh
        image_paths = []
        for root, dirs, files in os.walk(EVALUATION_DIR):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_paths.append(os.path.join(root, file))
                    
        if not image_paths:
            print(f"TRỐNG! Không tìm thấy bức ảnh nào trong {EVALUATION_DIR}")
            print("Hãy copy ảnh vào theo cấu trúc: evaluation_data/<MSSV>/anh1.jpg")
            return

        print(f"Bắt đầu chấm điểm trên {len(image_paths)} bức hình test...")
        start_time = time.time()
        
        for path in image_paths:
            # Tên thư mục cha chính là True Label (Ví dụ thư mục là UNKNOWN, hoặc là mã SV)
            true_label = os.path.basename(os.path.dirname(path))
            
            # Đọc ảnh (Hỗ trợ đường dẫn có tiếng Việt trên Windows)
            try:
                frame_data = np.fromfile(path, np.uint8)
                frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)
            except Exception:
                frame = None
                
            if frame is None:
                print(f"Lỗi: Không thể đọc ảnh {path}")
                continue
                
            # Đưa qua AI Extract
            results = detect_and_embed(frame)
            
            if len(results) == 0:
                # Không thấy khuôn mặt, AI cho rằng đây là vật thể lạ -> Trả về UNKNOWN
                pred_label = "UNKNOWN"
            else:
                # Lấy khuôn mặt to nhất (đầu tiên)
                embedding = results[0]['embedding']
                pred_label, sim = matcher.match(embedding)
            
            y_true.append(true_label)
            y_pred.append(pred_label)
            
            print(f"  [Test] Ảnh: {os.path.basename(path):<15} | Sự thật định danh: {true_label:<15} | AI đoán: {pred_label:<15} {'(SAI)' if true_label != pred_label else '(ĐÚNG)'}")

        end_time = time.time()
        
        # =============== TÍNH TOÁN VÀ XUẤT COMPONENT BÁO CÁO ================
        print("\n==================== KẾT QUẢ SYSTEM EVALUATION ====================")
        print(f"Tổng số ảnh test: {len(y_true)}")
        print(f"Tốc độ kiểm tra: {len(y_true)/(end_time-start_time):.2f} (fps/s)")
        
        # Tính cơ bản
        acc = accuracy_score(y_true, y_pred)
        # Macro (cào bằng danh tính) hoặc Weighted (trọng số theo lượng ảnh)
        prec = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        print(f"1. Accuracy (Độ chính xác) : {acc*100:.2f}%")
        print(f"2. Precision (Độ chuẩn xác): {prec*100:.2f}%")
        print(f"3. Recall (Độ thu hồi)     : {rec*100:.2f}%")
        print(f"4. F1-Score (Trung bình)   : {f1*100:.2f}%")
        print("===================================================================")
        
        # Trích lọc labels duy nhất để vẽ ma trận
        labels = sorted(list(set(y_true + y_pred)))
        cm = confusion_matrix(y_true, y_pred, labels=labels)
        
        # Vẽ đồ thị sử dụng seaborn
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=labels, yticklabels=labels, annot_kws={"size": 12})
        plt.title(f'Confusion Matrix (Accuracy: {acc*100:.1f}%)', fontsize=16)
        plt.xlabel('AI Predicted Label', fontsize=12)
        plt.ylabel('True Label (Sự thật)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        output_image = "evaluation_results.png"
        plt.savefig(output_image, dpi=300)
        print(f"[*] Đã xuất bản vẽ biểu đồ sắc nét (Dùng để đưa vào Word Báo Cáo): {output_image}")
        plt.show()

if __name__ == "__main__":
    if ensure_folders():
        run_evaluation()
