# HƯỚNG DẪN CÀI ĐẶT VÀ CẤU HÌNH HỆ THỐNG MTUFACE CHI TIẾT

Tài liệu này cung cấp hướng dẫn từng bước để cài đặt, cấu hình và khởi chạy toàn bộ hệ thống điểm danh nhận diện khuôn mặt **MTUFace**, bao gồm phần Backend (Flask + AI Core) và Mobile App (Flutter).

---

## 1. YÊU CẦU HỆ THỐNG (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các phần mềm sau:
- **Hệ điều hành**: Windows 10/11, macOS, hoặc Linux (Ubuntu).
- **Python**: Phiên bản `3.10` hoặc `3.11` (Không dùng bản 3.12+ do một số thư viện AI chưa hỗ trợ hoàn toàn).
- **Cơ sở dữ liệu**: MySQL Server 8.0+ (Khuyến nghị dùng [XAMPP](https://www.apachefriends.org/) để dễ quản lý cục bộ).
- **Git**: Dùng để clone mã nguồn dự án.
- **Flutter SDK**: Phiên bản `3.19` hoặc mới hơn (Dành cho Mobile App).
- **IDE**: Visual Studio Code, PyCharm, hoặc Android Studio.

---

## 2. CÀI ĐẶT BACKEND VÀ CƠ SỞ DỮ LIỆU

### Bước 2.1: Khởi tạo Cơ sở dữ liệu (MySQL)
1. Mở **XAMPP Control Panel** và Start **Apache** & **MySQL**.
2. Truy cập vào phpMyAdmin qua trình duyệt: `http://localhost/phpmyadmin/`.
3. Tạo một database mới với tên: `face_attendance_db` (Collation: `utf8mb4_unicode_ci`).
4. Import dữ liệu:
   - Chuyển sang tab **Import** (Nhập).
   - Chọn file `db/schema.sql` từ thư mục mã nguồn.
   - Bấm **Go** (Thực hiện) để tạo các bảng cần thiết.

### Bước 2.2: Cài đặt môi trường Python
1. Mở Terminal (Command Prompt / PowerShell) và di chuyển vào thư mục dự án gốc:
   ```bash
   cd NDKHM_DDSV_MTU
   ```
2. Tạo môi trường ảo (Virtual Environment):
   ```bash
   python -m venv .venv
   ```
3. Kích hoạt môi trường ảo:
   - Trên Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Trên macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```
4. Cài đặt các thư viện (Dependencies):
   ```bash
   pip install -r requirements.txt
   ```

### Bước 2.3: Thiết lập biến môi trường (.env)
1. Trong thư mục gốc, copy file `.env.example` và đổi tên thành `.env`.
2. Mở file `.env` lên và điền/chỉnh sửa các thông số sau:
   ```env
   # --- DATABASE CONFIG ---
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root          # Username MySQL của bạn (XAMPP thường là root)
   DB_PASSWORD=          # Mật khẩu MySQL (XAMPP thường để trống)
   DB_NAME=face_attendance_db

   # --- APP CONFIG ---
   SECRET_KEY=mot_chuoi_bi_mat_bat_ky_cua_ban
   FLASK_ENV=development
   PORT=5000

   # --- AI ENGINE ---
   # Chọn 1 trong 2: 'insightface' hoặc 'yolo_resnet'
   AI_ENGINE=insightface
   ```

### Bước 2.4: Tải và thiết lập Model AI
Hệ thống cần các file trọng số (Weights) để nhận diện. 
- Nếu dùng **InsightFace**, model sẽ tự động được tải xuống trong lần chạy đầu tiên.
- Nếu dùng **YOLO11**: File `yolo11n.pt` đã có sẵn trong thư mục gốc.

### Bước 2.5: Khởi chạy Backend Server
Từ Terminal (vẫn đang kích hoạt `.venv`), chạy lệnh:
```bash
python app.py
```
*Giao diện Web Admin đã sẵn sàng tại: http://localhost:5000*

---

## 3. CÀI ĐẶT VÀ CẤU HÌNH MOBILE APP (FLUTTER)

### Bước 3.1: Mở dự án Mobile
1. Khởi động Visual Studio Code hoặc Android Studio.
2. Mở thư mục `NDKHM_DDSV_MTU/mobile_flutter`.
3. Mở Terminal trong VS Code và tải các package:
   ```bash
   flutter pub get
   ```

### Bước 3.2: Cấu hình kết nối API
Để điện thoại có thể gọi đến Backend trên máy tính, bạn cần đổi IP Local:
1. Mở Terminal trên Windows (cmd), gõ `ipconfig` để lấy **IPv4 Address** của máy tính (Ví dụ: `192.168.1.10`).
2. Mở file `mobile_flutter/lib/services/api_service.dart`.
3. Tìm biến chứa URL API và sửa thành IP của bạn:
   ```dart
   static const String baseUrl = 'http://192.168.1.10:5000/api';
   // KHÔNG dùng localhost hoặc 127.0.0.1 vì điện thoại sẽ hiểu là chính nó
   ```

### Bước 3.3: Cấu hình Firebase (Cho Push Notifications - Nếu có)
*Lưu ý: Nếu không cần gửi thông báo đẩy đến điện thoại, có thể bỏ qua bước này.*
1. Đăng nhập [Firebase Console](https://console.firebase.google.com/) và tạo Project mới.
2. Cài đặt Firebase CLI và cấu hình dự án Flutter của bạn qua lệnh `flutterfire configure`.
3. Thay thế file `serviceAccountKey.json` ở backend (nếu dùng FCM từ backend) bằng file lấy từ Firebase Console của bạn.

### Bước 3.4: Chạy ứng dụng trên thiết bị
- Kết nối điện thoại thật qua cáp USB (đã bật chế độ Gỡ lỗi USB/Developer Mode) hoặc bật máy ảo Emulator.
- Chạy ứng dụng:
  ```bash
  flutter run
  ```

---

## 4. THIẾT LẬP NÂNG CAO & TÍCH HỢP

### 4.1. Tích hợp Camera IP (Imou / RTSP)
Để Kiosk có thể nhận diện qua Camera IP thay vì Webcam máy tính:
1. Vào Web Admin -> Tab **Cấu hình Camera**.
2. Nhập URL RTSP của Camera (Ví dụ: `rtsp://admin:MậtKhẩuCủaBạn@192.168.1.20:554/cam/realmonitor?channel=1&subtype=0`).
3. Lưu lại và hệ thống sẽ tự động chuyển sang luồng camera IP (Độ trễ được tối ưu qua OpenCV Threading).

### 4.2. Cấu hình Cảnh báo Telegram / Zalo
Nếu muốn nhận thông báo khi có người lạ hoặc điểm danh thành công:
- **Telegram**: Tạo Bot qua `@BotFather`, lấy `Bot Token` và `Chat ID`. Điền vào file `.env`:
  ```env
  TELEGRAM_BOT_TOKEN=your_bot_token
  TELEGRAM_CHAT_ID=your_chat_id
  ```
- **Zalo ZNS**: Đăng ký Zalo OA, lấy `Access Token` và thiết lập trong `services/telegram_alert.py` (hoặc file Zalo Service tương ứng).

### 4.3. Chuyển đổi Engine AI (InsightFace <-> YOLO11)
Bạn có thể thay đổi Engine AI không cần restart server bằng cách vào trang **Huấn Luyện** trên Web Admin và chọn Engine tương ứng trong phần Cài đặt AI.

---

## 5. HƯỚNG DẪN DEPLOY LÊN SERVER (DOCKER)

Để đưa hệ thống lên Production (VPS/Cloud) một cách nhanh chóng, sử dụng Docker:

1. Đảm bảo server đã cài đặt `Docker` và `Docker Compose`.
2. Mở file `.env`, đổi `DB_HOST` thành tên service của database trong Docker:
   ```env
   DB_HOST=db
   ```
3. Chạy lệnh:
   ```bash
   docker-compose up -d --build
   ```
Hệ thống sẽ tự động build image Flask, pull image MySQL, khởi tạo CSDL và chạy ở port `5000`.

---
**Chúc bạn cài đặt thành công và trải nghiệm MTUFace!** Nếu gặp lỗi `WinError 5` hoặc các vấn đề truy cập camera, hãy chạy Terminal/IDE bằng quyền Administrator (Run as Admin).
