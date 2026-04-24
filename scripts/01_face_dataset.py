"""
BƯỚC 1: CÔNG CỤ THU THẬP KHUÔN MẶT CỤC BỘ (Dataset Builder)
Sử dụng Camera để quay 50 khung hình các góc độ khuôn mặt, giúp AI nhận diện cực chính xác.
"""

import cv2
import os
import db_handler

DATABASE_DIR = "database"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

print("="*40)
print("HỆ THỐNG ĐĂNG KÝ KHUÔN MẶT SINH VIÊN")
print("="*40)

# Nhập liệu
face_id = input("\n[1] Nhập Mã số Nhân sự / Sinh viên (Viết liền ko dấu): ").strip()
face_name = input("[2] Nhập Họ và Tên (Tiếng Việt): ").strip()

if not face_id or not face_name:
    print("[LỖI] Dữ liệu không hợp lệ. Thoát!")
    exit()

print(f"\n[INFO] Đang mở Camera... Hãy nhìn thẳng vào ống kính.")
print(f"       ==> NHẤN PHÍM 'SPACE' ĐỂ BẮT ĐẦU CHỤP LIÊN TỤC 50 TẤM.")
print(f"       ==> NHẤN PHÍM 'ESC' ĐỂ HỦY BỎ.")

cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    if not ret:
        print("[LỖI] Không thể đọc luồng Camera.")
        break
        
    frame = cv2.flip(frame, 1) # Lật ảnh
    display_frame = frame.copy()
    
    cv2.putText(display_frame, f"Nhan 'SPACE' de CHUP 50 anh cho {face_id}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    cv2.imshow("Buoc 1: Thu Thap Du Lieu (Nhan SPACE)", display_frame)

    k = cv2.waitKey(1) & 0xFF
    if k == 27: # ESC
        print("\n[INFO] Hủy bỏ thu thập.")
        break
    elif k == 32: # SPACE
        print("\n[INFO] Bắt đầu thu thập 50 mẫu! Vui lòng xoay nhẹ đầu sang trái, phải, lên, xuống...")
        count = 0
        
        # Đưa thông tin vào Database định danh
        db_handler.init_database_if_not_exists()
        # Lưu tấm số 0 làm Avatar đại diện
        db_handler.add_student(face_id, face_name, f"{face_id}_0.jpg")
        
        while count < 50:
            ret, frame = cam.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            
            # Ghi file
            filename = f"{face_id}_{count}.jpg"
            filepath = os.path.join(DATABASE_DIR, filename)
            cv2.imwrite(filepath, frame)
            
            # Hiển thị trên màn hình tiến độ
            cv2.putText(frame, f"Dang chup: {count+1}/50", (20, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Buoc 1: Thu Thap Du Lieu (Nhan SPACE)", frame)
            
            # Delay một tí để người dùng kịp đổi góc đầu (100ms)
            cv2.waitKey(100) 
            count += 1
            
        print(f"\n[THÀNH CÔNG] Đã lưu {count} mẫu hình ảnh góc độ khác nhau vào kho '{DATABASE_DIR}'.")
        print(f"             Cập nhật CSDL MySQL thành công: {face_name}")
        print(f"\n👉 LỜI KHUYÊN: Hãy chạy file '02_face_training.py' để nén toàn bộ 50 ảnh này thành 1 vector Não Bộ!")
        break

cam.release()
cv2.destroyAllWindows()
