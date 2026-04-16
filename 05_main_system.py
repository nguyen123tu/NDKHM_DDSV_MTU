import cv2
import numpy as np
import time
import os
import glob
from ultralytics import YOLO
from insightface.app import FaceAnalysis

# Import module tự viết
from telegram_alert import send_telegram_photo

# =========================================================================
# 1. CẤU HÌNH THÔNG SỐ (CONFIGURATION)
# =========================================================================
DATABASE_DIR = "database"
SIMILARITY_THRESHOLD = 0.45    # Ngưỡng nhận diện mặt (cosine)
MOTION_AREA_THRESHOLD = 3000   # Diện tích thay đổi nhỏ nhất để tính là có chuyển động
ALERT_COOLDOWN_SEC = 20        # Không gửi Telegram liên tiếp trong 20 giây

# Variables State
last_alert_time = 0
known_faces = {}               # Dictionary chứa {Tên: Face_Embedding_Vector}

# =========================================================================
# 2. KHỞI TẠO MÔ HÌNH VÀ TẢI DATA GỐC
# =========================================================================
print("[INFO] Bắt đầu khởi tạo hệ thống...")

# Khởi tạo mô hình phát hiện chuyển động (Background Subtractor MOG2)
bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)

# Khởi tạo YOLOv8 (tự tải file yolov8n.pt chuẩn về nếu chưa có)
print("[INFO] Khởi tạo YOLOv8...")
yolo_model = YOLO("yolov8n.pt") # Dùng bản 'n' (nano) rất nhẹ để chạy Realtime mượt

# Khởi tạo InsightFace
print("[INFO] Khởi tạo InsightFace...")
app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

# Quét và trích xuất đặc điểm người nhà/sinh viên
print("[INFO] Đang tải danh sách người quen trong CSDL...")
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

# Quét thư mục con (cấu trúc mới: database/MSSV/*.jpg)
subdirs = [d for d in os.listdir(DATABASE_DIR) if os.path.isdir(os.path.join(DATABASE_DIR, d))]
for ma_sv_dir in subdirs:
    student_path = os.path.join(DATABASE_DIR, ma_sv_dir)
    image_files = glob.glob(os.path.join(student_path, "*.jpg")) + glob.glob(os.path.join(student_path, "*.png"))
    for image_path in image_files:
        img = cv2.imread(image_path)
        if img is not None:
            faces = app.get(img)
            if len(faces) > 0:
                known_faces[ma_sv_dir] = faces[0].embedding
                print(f" ==> Đã học thuộc khuôn mặt: {ma_sv_dir}")
                break  # Chỉ cần 1 ảnh tốt nhất cho mỗi SV ở chế độ standalone

# Fallback: Quét ảnh phẳng cũ ở root database/ (tương thích ngược)
for image_path in glob.glob(os.path.join(DATABASE_DIR, "*.jpg")) + glob.glob(os.path.join(DATABASE_DIR, "*.png")):
    name = os.path.splitext(os.path.basename(image_path))[0]
    img = cv2.imread(image_path)
    if img is not None:
        faces = app.get(img)
        if len(faces) > 0:
            known_faces[name] = faces[0].embedding
            print(f" ==> Đã học thuộc khuôn mặt (ảnh cũ): {name}")

if len(known_faces) == 0:
    print("[CẢNH BÁO] Thư mục 'database' chưa có thư mục ảnh nào hợp lệ để nhận diện.")

print("[INFO] HỆ THỐNG ĐÃ SẴN SÀNG RUN!")

# =========================================================================
# 3. QUÁ TRÌNH CHẠY CHÍNH (MAIN Pipeline)
# =========================================================================
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    # a. KIỂM TRA CHUYỂN ĐỘNG BẰNG OPENCV
    fg_mask = bg_subtractor.apply(frame)
    # Khử nhiễu cơ bản
    _, fg_mask = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    motion_area = cv2.countNonZero(fg_mask)
    
    # Hiển thị icon trạng thái ban đầu
    status_text = "Status: IDLE"
    status_color = (150, 150, 150) # Xám
    
    # Nếu diện tích mảng sáng (pixel chuyển động) lớn hơn Ngưỡng
    if motion_area > MOTION_AREA_THRESHOLD:
        status_text = "Status: MOTION DETECTED"
        status_color = (0, 165, 255) # Cam
        
        # b. CHẠY YOLOv8 ĐỂ TÌM XEM CHUYỂN ĐỘNG CÓ PHẢI LÀ NGƯỜI KHÔNG
        # Chạy dự đoán, chỉ lấy đối tượng (class=0 là Person ở COCO model)
        results = yolo_model(frame, classes=[0], stream=True, verbose=False)
        person_detected = False
        
        for r in results:
            boxes = r.boxes
            if len(boxes) > 0:
                person_detected = True
                break
                
        # Nếu phát hiện người (Class 0)
        if person_detected:
            status_text = "Status: PERSON DETECTED -> RECOGNIZING"
            status_color = (0, 255, 255) # Vàng
            
            # c. TRÍCH XUẤT FACE RECOGNITION VÀ SO SÁNH
            # Phân tích khuôn mặt trên toàn bộ bức ảnh
            faces = app.get(frame)
            
            for face in faces:
                best_match_name = "Kẻ Lạ (Unknown)"
                best_similarity = 0.0
                face_emb = face.embedding
                
                # Tính bounding box của mặt để vẽ Draw (box có cấu trúc left, top, right, bottom)
                x1, y1, x2, y2 = face.bbox.astype(int)
                
                # So sánh với CSDL trong RAM
                for name, known_emb in known_faces.items():
                    similarity = np.dot(face_emb, known_emb) / (np.linalg.norm(face_emb) * np.linalg.norm(known_emb))
                    if similarity > best_similarity:
                        best_similarity = similarity
                        if similarity > SIMILARITY_THRESHOLD:
                            best_match_name = name
                
                # Dựng hiển thị (Vẽ Box)
                color = (0, 255, 0) if best_match_name != "Kẻ Lạ (Unknown)" else (0, 0, 255)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{best_match_name} ({best_similarity:.2f})", (x1, y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                # d. XỬ LÝ LOGIC CẢNH BÁO TELEGRAM
                if best_match_name == "Kẻ Lạ (Unknown)":
                    current_time = time.time()
                    if current_time - last_alert_time > ALERT_COOLDOWN_SEC:
                        # Gửi Alert khi giãn đủ khoảng cách thời gian
                        print("[ALERT] Phát hiện người lạ, chuẩn bị gửi báo động!")
                        send_telegram_photo(frame, message="🚨 CẢNH BÁO BẢO MẬT: Phát hiện Người Lạ lọt vào khu vực Camera!")
                        last_alert_time = current_time

    # Vẽ trạng thái tổng lưu lượng luồng lên màn hình
    cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    # Hiển thị
    cv2.imshow("He Thong AI Đo An Tot Nghiep", frame)
    # Mở một cửa sổ nhỏ để bạn xem cách Mask nhận diện chuyển động hoạt động (Debug)
    # cv2.imshow("Mask Chuyen Đong", fg_mask) 
    
    # Bấm Q để thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
