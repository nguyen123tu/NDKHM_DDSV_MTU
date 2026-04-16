import cv2
import requests
import io

# THIẾT LẬP THÔNG SỐ TELEGRAM
# Bạn thay thế bằng Token và Chat ID của bạn ở đây
TELEGRAM_BOT_TOKEN = "8762386247:AAEBvm2-qGIXf2T8gsiK5n8hXxlqqwak39c"
TELEGRAM_CHAT_ID = "7724279500"

def send_telegram_photo(frame, message="Phát hiện đối tượng!"):
    """
    Gửi khung hình ảnh và thông báo tới Telegram qua HTTP API.
    Tuy nhiên, nếu chưa điền Token, hàm sẽ chỉ in ra màn hình.
    """
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID" or not TELEGRAM_BOT_TOKEN:
        print(f"[CẢNH BÁO TELEGRAM MÔ PHỎNG] Tin nhắn: {message}")
        print("=> Bạn chưa cấu hình Token Telegram nên không thể gửi thật.")
        return False
        
    try:
        # Encode OpenCV frame (BGR) to JPG format in memory
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Lỗi khi nén ảnh để gửi Telegram.")
            return False
            
        io_buf = io.BytesIO(buffer)
        io_buf.name = "alert.jpg"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        data = {"chat_id": TELEGRAM_CHAT_ID, "caption": message}
        files = {"photo": io_buf}

        response = requests.post(url, data=data, files=files)
        
        if response.status_code == 200:
            print("[TELEGRAM] Đã gửi thông báo thành công!")
            return True
        else:
            print(f"[TELEGRAM LỖI] HTTP {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"[TELEGRAM LỖI] Lỗi kết nối gửi ảnh: {e}")
        return False

# Chạy thử nếu chạy trực tiếp file này (không gọi qua thư viện khác)
if __name__ == "__main__":
    import numpy as np
    # Tạo một ảnh rỗng đen để gửi thử
    test_img = np.zeros((300, 300, 3), dtype=np.uint8)
    # Lệnh sẽ mô phỏng hoặc gửi nếu đã điền mã
    send_telegram_photo(test_img, "Test tin nhắn báo động!")
