# 🎓 MTUFace - Hệ Thống Điểm Danh Bằng Nhận Diện Khuôn Mặt (Face Recognition Attendance)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B.svg)](https://flutter.dev/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Backend-black.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-Database-orange.svg)](https://www.mysql.com/)

**MTUFace** là hệ thống quản lý điểm danh thông minh sử dụng công nghệ nhận diện khuôn mặt Deep Learning, hỗ trợ đa engine AI (InsightFace, DeepFace/ArcFace, YOLO + ResNet). Hệ thống bao gồm 3 thành phần chính:

1. **Web Admin Dashboard** (Flask + SocketIO): Giao diện quản lý cho quản trị viên với thiết kế Glassmorphism hiện đại, giám sát theo thời gian thực (Kiosk HUD), AI Chatbot hỗ trợ, và hệ thống cảnh báo gian lận.
2. **AI Core Engine**: Pipeline nhận diện khuôn mặt đa engine — hỗ trợ chuyển đổi nóng giữa InsightFace, DeepFace (ArcFace + RetinaFace), và YOLO + ResNet. Tích hợp Liveness Detection chống giả mạo.
3. **Mobile App** (Flutter): Ứng dụng di động "Offline-first" dành cho sinh viên để tra cứu lịch sử điểm danh, xem thông tin cá nhân và đăng ký khuôn mặt tự động, hỗ trợ đồng bộ dữ liệu.

---

## 🌟 Tính Năng Nổi Bật

### 🤖 AI & Nhận Diện
- **Đa engine AI**: Chuyển đổi nóng giữa InsightFace, DeepFace (ArcFace + RetinaFace), YOLO + ResNet — không cần restart server.
- **Nhận diện khuôn mặt theo thời gian thực**: Phát hiện và nhận dạng khuôn mặt qua webcam với độ trễ thấp (<100ms).
- **Liveness Detection**: Phát hiện gian lận bằng phân tích blur, glare, kích thước khuôn mặt — chống ảnh/video giả mạo.
- **YOLO26 Training**: Script huấn luyện mô hình phát hiện khuôn mặt với YOLO26 (MuSGD optimizer, NMS-free inference).
- **AI Chatbot**: Trợ lý AI thông minh tích hợp ChromaDB, hỗ trợ truy vấn thông tin sinh viên và thống kê điểm danh.

### 🖥️ Web Admin Dashboard
- **Giao diện Glassmorphism**: Thiết kế hiện đại, dark theme, hiệu ứng kính mờ cao cấp trên toàn bộ hệ thống.
- **Kiosk HUD thông minh**: Giao diện check-in chuyên nghiệp (Auto / In / Out mode) với camera tracking và feedback trực quan.
- **Self-Check công khai**: Trang điểm danh tự phục vụ cho sinh viên, không cần đăng nhập.
- **Quản lý lớp học & lịch học**: Tạo, sửa, xóa lớp học và quản lý lịch học theo tuần.
- **Cảnh báo gian lận**: Trang giám sát các lần phát hiện gian lận với log chi tiết.
- **Kết xuất báo cáo**: Xuất dữ liệu điểm danh ra file Excel/PDF.
- **Thông báo Telegram**: Cảnh báo tự động qua Telegram Bot khi phát hiện người lạ hoặc hành vi bất thường.

### 📱 Mobile App (Flutter)
- **Offline-first**: Dữ liệu lưu trữ cục bộ (SQLite), đồng bộ với server khi có mạng.
- **Xem lịch sử điểm danh**: Tra cứu chi tiết từng buổi học.
- **Quản lý phiên điểm danh**: Admin có thể tạo và giám sát phiên điểm danh từ mobile.
- **QR Scanner**: Quét mã QR cho điểm danh nhanh.
- **Thông báo push**: Nhận thông báo khi điểm danh thành công.

---

## 📂 Cấu Trúc Dự Án (Project Architecture)

```text
NDKHM_DDSV_MTU/
├── app.py                  # Flask application factory & entry point
├── config.py               # Cấu hình hệ thống (đọc từ .env)
├── core/                   # AI Core Engine
│   ├── engine.py           # Engine chính (InsightFace / YOLO+ResNet)
│   ├── engine_deepface.py  # Engine DeepFace (ArcFace + RetinaFace)
│   ├── detector.py         # Face detector (InsightFace)
│   ├── detector_yolo.py    # Face detector (YOLO)
│   ├── embedder.py         # Face embedder (InsightFace)
│   ├── embedder_resnet.py  # Face embedder (ResNet)
│   ├── matcher.py          # So khớp vector khuôn mặt
│   ├── trainer.py          # Huấn luyện & đăng ký khuôn mặt
│   └── camera.py           # Quản lý camera/webcam
├── db/                     # Database schemas (MySQL), migrations
│   ├── connection.py       # Connection pool MySQL
│   ├── schema.sql          # Schema chính
│   └── migrations/         # Các file migration SQL
├── routes/                 # Controllers — Web routes & Mobile APIs
│   ├── api_mobile.py       # RESTful API cho Flutter App
│   ├── attendance.py       # Điểm danh (live, history)
│   ├── auth.py             # Đăng nhập / Xác thực
│   ├── chatbot.py          # AI Chatbot endpoint
│   ├── classes.py          # Quản lý lớp học
│   ├── dashboard.py        # Trang chủ Admin
│   ├── deepface_api.py     # API riêng cho DeepFace engine
│   ├── export.py           # Xuất báo cáo Excel/PDF
│   ├── fraud.py            # Cảnh báo gian lận
│   ├── public.py           # Trang công khai (selfcheck, tra cứu)
│   ├── students.py         # Quản lý sinh viên
│   └── training.py         # Huấn luyện mô hình AI
├── services/               # Business logic layer
│   ├── recognition_thread.py   # Luồng nhận diện realtime
│   ├── attendance_service.py   # Nghiệp vụ điểm danh
│   ├── student_service.py      # Nghiệp vụ sinh viên
│   ├── ai_chatbot.py           # AI Chatbot (ChromaDB)
│   ├── knowledge_builder.py    # Xây dựng knowledge base
│   ├── export_service.py       # Xuất báo cáo
│   └── telegram_alert.py      # Gửi cảnh báo Telegram
├── mobile_flutter/         # Source code Flutter Mobile App
├── static/                 # Assets tĩnh
│   ├── css/
│   │   ├── main.css        # CSS chung (design system)
│   │   ├── components/     # CSS components (ai_assistant...)
│   │   └── pages/          # CSS riêng từng trang
│   ├── js/
│   │   ├── components/     # JS components (ai_assistant...)
│   │   └── pages/          # JS riêng từng trang
│   └── img/                # Hình ảnh, logo, favicon
├── templates/              # Giao diện Jinja2 cho Web Admin
│   ├── base.html           # Layout chính
│   ├── dashboard/          # Trang chủ, kiosk, fraud alerts
│   ├── attendance/         # Live & History
│   ├── students/           # CRUD sinh viên
│   ├── classes/            # Quản lý lớp, lịch học
│   ├── chatbot/            # Giao diện AI Chatbot
│   ├── training/           # Huấn luyện mô hình
│   ├── public/             # Selfcheck, tra cứu công khai
│   └── export/             # Xuất báo cáo
├── tools/                  # Công cụ hỗ trợ
│   ├── convert_onnx_to_tflite.py  # Chuyển đổi model cho mobile
│   └── download_models.py        # Tải model AI
├── train_yolo26.py         # Script huấn luyện YOLO26
├── requirements.txt        # Thư viện Python dependencies
├── Dockerfile              # Docker image cho backend
├── docker-compose.yml      # Docker Compose (backend + MySQL)
└── .env.example            # File cấu hình biến môi trường mẫu
```

---

## 🚀 Hướng Dẫn Cài Đặt (Setup Guide)

### 1. Yêu Cầu Hệ Thống (Prerequisites)
- **Python**: Phiên bản 3.10 trở lên.
- **Cơ sở dữ liệu**: MySQL 8.x (Có thể dùng XAMPP để dễ dàng quản lý cục bộ).
- **Flutter SDK**: Để build và chạy ứng dụng mobile (tuỳ chọn).
- **Webcam**: Camera USB hoặc webcam tích hợp cho nhận diện khuôn mặt.

### 2. Thiết Lập Môi Trường Backend (Flask & AI)

**Bước 1:** Clone dự án và tạo Virtual Environment
```bash
git clone https://github.com/nguyen123tu/NDKHM_DDSV_MTU.git
cd NDKHM_DDSV_MTU
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
- Lựa chọn engine AI:
  - `AI_ENGINE=insightface` — InsightFace (mặc định, nhanh, chính xác cao)
  - `AI_ENGINE=yolo_resnet` — YOLO + ResNet
  - `AI_ENGINE=deepface` — DeepFace (ArcFace + RetinaFace, hỗ trợ anti-spoofing)
- Thêm Telegram Bot Token nếu muốn nhận thông báo realtime.

**Bước 4:** Khởi tạo Cơ sở dữ liệu
- Import file `db/schema.sql` vào MySQL:
```bash
mysql -u root -p face_attendance_db < db/schema.sql
```
- Nếu cần thêm bảng phiên điểm danh:
```bash
mysql -u root -p face_attendance_db < db/migrations/add_phien_diem_danh.sql
```

### 3. Chạy Hệ Thống Backend
Khởi động Web server và Engine AI:
```bash
python app.py
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
> **Lưu ý**: Đảm bảo thiết bị di động cùng mạng (LAN) với máy chủ và cấu hình đúng địa chỉ IP máy chủ API trong `mobile_flutter/lib/services/api_service.dart`. Nếu gặp lỗi Firewall Windows, vui lòng mở port 5000 ở Inbound Rules.

---

## 🔧 Chuyển Đổi Engine AI

Hệ thống hỗ trợ chuyển đổi nóng giữa các engine AI ngay trên giao diện web (trang **Huấn luyện**), hoặc cấu hình trong file `.env`:

| Engine | Model | Detector | Ưu điểm |
|--------|-------|----------|----------|
| `insightface` | buffalo_l | InsightFace | Nhanh, chính xác cao, ổn định |
| `deepface` | ArcFace | RetinaFace | Hỗ trợ anti-spoofing, phân tích tuổi/giới tính |
| `yolo_resnet` | YOLOv11 + ResNet | YOLO | Tuỳ chỉnh linh hoạt, train được trên dataset riêng |

---

## 🔒 Bảo Mật & Lưu Ý Quan Trọng
- **KHÔNG** commit file `.env` chứa token thật, cấu hình mật khẩu database lên public repository.
- Các mô hình AI (`.pth`, `.onnx`, `.pt`) và thư mục dữ liệu cá nhân (`database/`, `dataset/`) có dung lượng lớn và đã được cấu hình trong `.gitignore`.
- Nếu Telegram bot token bị lộ, hãy vào `@BotFather` để revoke/thay đổi ngay lập tức.
- Đối với Production, hãy cân nhắc sử dụng Nginx/Gunicorn và thiết lập HTTPS.

---

## 🐳 Docker Deployment (Tuỳ chọn)

Hệ thống hỗ trợ chạy bằng Docker để đồng bộ hoá môi trường trên Server Production:

```bash
docker-compose up --build -d
```

> **Lưu ý**: Khi chạy Docker, `DB_HOST` sẽ được override thành `db` (tên service MySQL trong docker-compose). Hãy cập nhật `DB_PASSWORD` trong file `.env` cho phù hợp.

---

## 📄 Giấy Phép (License)

Dự án được phát triển phục vụ đồ án tốt nghiệp tại **Trường Đại học Xây dựng Miền Tây (MTU)**.

© 2024-2026 MTUFace Team
