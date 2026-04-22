import cv2
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("CAMERA_SOURCE")

print(f"Đang kiểm tra kết nối tới: {url}")
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("X Lỗi: Không thể mở luồng Video. Hãy kiểm tra:")
    print("  1. ESP32-CAM có đang bật không?")
    print("  2. Bạn có đang mở trang web xem camera trên Chrome/Cốc Cốc không? (Hãy TẮT NÓ ĐI)")
    print("  3. Hai thiết bị có chung WiFi không?")
else:
    print("V Thành công! Đang hiển thị cửa sổ test...")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Mất kết nối...")
            break
        cv2.imshow("Test Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
