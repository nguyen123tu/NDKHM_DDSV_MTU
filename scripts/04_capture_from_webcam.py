import cv2
import os

def capture_image(save_name="anh_chuan.jpg"):
    # Mở camera (số 0 thường là camera mặc định trên laptop)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Không thể mở Webcam. Hãy chắc chắn bạn có camera.")
        return

    print("=== HƯỚNG DẪN CƠ BẢN ===")
    print("1. Nhìn thẳng vào camera")
    print("2. Nhấn phím MỘT LẦN phím SPACE (Khoảng trắng) để CHỤP VÀ LƯU ẢNH.")
    print("3. Nhấn phím 'q' hoặc 'ESC' để THEO RÚT (Thoát).")
    
    while True:
        # Đọc từng khung hình từ camera
        ret, frame = cap.read()
        if not ret:
            print("Không thể nhận diện khung hình, đang thoát...")
            break

        # Hiển thị khung hình lên màn hình
        cv2.imshow("Capture Image (Nhan SPACE de chup, Q de thoat)", frame)

        # Chờ phím bấm (1 mili-giây cho mỗi khung hình)
        key = cv2.waitKey(1) & 0xFF

        # Nếu nhấn phím SPACE (mã ASCII là 32)
        if key == 32:
            # Lưu khung hình hiện tại thành file ảnh
            cv2.imwrite(save_name, frame)
            print(f"✅ Đã chụp và lưu ảnh thành công vào file: {os.path.abspath(save_name)}")
            break # Chụp xong thì thoát luôn

        # Nếu nhấn phím q (thoát) hoặc ESC (mã 27)
        elif key == ord('q') or key == 27:
            print("Đã hủy chụp ảnh.")
            break

    # Dọn dẹp: tắt camera và đóng cửa sổ
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Chạy hàm chụp ảnh, tự động lưu tên file là 'anh_chuan.jpg'
    capture_image("anh_chuan.jpg")
