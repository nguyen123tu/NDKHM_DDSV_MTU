# 🎓 MTUFace - Hệ Thống Điểm Danh Bằng Nhận Diện Khuôn Mặt (Face Recognition Attendance)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B.svg)](https://flutter.dev/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Backend-black.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-Database-orange.svg)](https://www.mysql.com/)

**MTUFace** là hệ thống quản lý điểm danh thông minh sử dụng công nghệ nhận diện khuôn mặt Deep Learning (YOLOv11, ResNet, InsightFace). Hệ thống bao gồm 3 thành phần chính:
1. **Web Admin Dashboard** (Flask + SocketIO): Giao diện quản lý cho quản trị viên, giám sát theo thời gian thực (Kiosk HUD).
2. **AI Core Engine**: Pipeline nhận diện khuôn mặt mạnh mẽ, tối ưu hóa cho độ trễ thấp và độ chính xác cao.
3. **Mobile App** (Flutter): Ứng dụng di động "Offline-first" dành cho sinh viên để tra cứu lịch sử điểm danh, xem thông tin cá nhân và đăng ký khuôn mặt tự động, hỗ trợ đồng bộ dữ liệu.

---

## 🌟 Tính Năng Nổi Bật

- **Nhận diện khuôn mặt theo thời gian thực**: Sử dụng mô hình YOLOv11 và ResNet/InsightFace để phát hiện và nhận dạng khuôn mặt trong tích tắc.
- **Kiosk HUD thông minh**: Giao diện check-in chuyên nghiệp (Auto / In / Out mode) chia cột camera và thông tin sinh viên rõ ràng.
- **Mobile App đồng bộ Offline**: Sinh viên có thể xem lịch sử, thông báo điểm danh trên ứng dụng điện thoại. Dữ liệu được lưu trữ cục bộ (SQLite) và đồng bộ với server khi có mạng.
- **Hệ thống cảnh báo tự động**: Thông báo qua Telegram (Telegram Bot) khi phát hiện người lạ chưa được đăng ký hoặc có hành vi bất thường.
- **Quản trị viên đa năng**: Xét duyệt sinh viên đăng ký mới, quản lý lịch học, kết xuất báo cáo thống kê qua file Excel/PDF.

---

## 📂 Cấu Trúc Dự Án (Project Architecture)

Xem chi tiết tại `docs/PROJECT_STRUCTURE.md`.

```text
NDKHM_DDSV_MTU/
├── app.py                # Flask application factory
├── run_server.py         # Entry point chạy server chính (API + Web)
├── core/                 # AI Core (xử lý mô hình YOLO, ResNet, InsightFace)
├── db/                   # Database schemas (MySQL), kết nối và seeders
├── routes/               # Controllers xử lý Web routes & Mobile APIs
├── services/             # Business logic (Student, Attendance, Telegram Alert...)
├── mobile_flutter/       # Source code Flutter Mobile App
├── static/               # Assets (CSS, JS, Images, Logo MTU)
├── templates/            # Giao diện Jinja2 cho Web Admin
├── scripts/              # Các script hỗ trợ, tool CLI, training models
├── requirements.txt      # Thư viện Python dependencies
└── .env.example          # File cấu hình biến môi trường mẫu
```

---

## 🚀 Hướng Dẫn Cài Đặt (Setup Guide)

### 1. Yêu Cầu Hệ Thống (Prerequisites)
- **Python**: Phiên bản 3.10 trở lên.
- **Cơ sở dữ liệu**: MySQL 8.x (Có thể dùng XAMPP để dễ dàng quản lý cục bộ).
- **Flutter SDK**: Để build và chạy ứng dụng mobile.

### 2. Thiết Lập Môi Trường Backend (Flask & AI)

**Bước 1:** Clone dự án và tạo Virtual Environment
```bash
python -m venv .venv
# Kích hoạt trên Windows:
.venv\Scripts\activate
# Kích hoạt trên Linux/macOS:
source .venv/bin/activate
```

**Bước 2:** Cài đặt thư viện Python
```bash
pip install -r requirements.txt
```

**Bước 3:** Cấu hình biến môi trường
- Sao chép file `.env.example` thành `.env`
- Cập nhật các thông số Database (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
- Lựa chọn engine AI: `AI_ENGINE=insightface` hoặc `yolo_resnet`.
- Thêm Telegram Bot Token nếu muốn nhận thông báo realtime.

**Bước 4:** Khởi tạo Cơ sở dữ liệu
```bash
python scripts/init_db.py
```

### 3. Chạy Hệ Thống Backend
Khởi động Web server và Engine AI bằng câu lệnh:
```bash
python run_server.py
```
> 🌐 Truy cập Web Admin Dashboard tại: `http://localhost:5000`

---

## 📱 Khởi Động Mobile App (Flutter)

Mobile app được đặt trong thư mục `mobile_flutter/`. Bạn cần cắm thiết bị thật hoặc mở máy ảo Simulator/Emulator.

```bash
cd mobile_flutter
flutter pub get
flutter run
```
> **Lưu ý**: Đảm bảo thiết bị di động cùng mạng (LAN) với máy chủ và cấu hình đúng địa chỉ IP máy chủ API trong thư mục mobile_flutter. Nếu gặp lỗi Firewall Windows, vui lòng mở port 5000 ở Inbound Rules.

---

## 🔒 Bảo Mật & Lưu Ý Quan Trọng
- **KHÔNG** commit file `.env` chứa token thật, cấu hình mật khẩu database lên public repository.
- Các mô hình AI (.pth, .onnx, .pt) và thư mục dữ liệu cá nhân (`/data/faces/`) thường có dung lượng lớn, hãy cẩn thận khi cấu hình `.gitignore`.
- Nếu Telegram bot token bị lộ, hãy vào `@BotFather` để revoke/thay đổi ngay lập tức.
- Đối với Production, hãy cân nhắc sử dụng Nginx/Gunicorn và thiết lập HTTPS.

---

## 🐳 Docker Deployment (Tuỳ chọn)

Hệ thống hỗ trợ chạy bằng Docker để đồng bộ hoá môi trường tốt hơn trên Server Production. Cấu hình có sẵn tại `Dockerfile` và `docker-compose.yml`.

```bash
docker-compose up --build -d
```
