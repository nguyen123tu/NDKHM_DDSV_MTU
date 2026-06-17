# 🎓 MTUFace - Hệ Thống Điểm Danh Bằng Nhận Diện Khuôn Mặt Thông Minh

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B.svg)](https://flutter.dev/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Backend-black.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

**MTUFace** là hệ thống quản lý điểm danh toàn diện, kết hợp Web Admin Dashboard và Mobile App "Offline-first", sử dụng các công nghệ trí tuệ nhân tạo (Deep Learning) hàng đầu hiện nay. Hệ thống được thiết kế để chống gian lận, tốc độ nhận diện cao và dễ dàng triển khai.

## 🌟 Tính Năng Nổi Bật

### 🤖 Lõi AI Đa Nền Tảng (Multi-Engine AI Core)
- **Kiến trúc Factory linh hoạt**: Hỗ trợ chuyển đổi "nóng" giữa 3 nền tảng AI mạnh mẽ thông qua file `.env` hoặc Web Admin:
  1. **InsightFace** (`buffalo_l` / `buffalo_sc`): Tốc độ siêu nhanh, độ chính xác nhận diện (Face Verification) chuẩn công nghiệp.
  2. **YOLO11 + ResNet50**: Nhận diện tuỳ chỉnh với YOLO11 (MuSGD optimizer) và Embedding bằng ResNet50.
  3. **DeepFace**: Hỗ trợ đa dạng models (ArcFace, Facenet512, GhostFaceNet, v.v.).
- **Chống Giả Mạo & Liveness Detection (Anti-Spoofing)**:
  - Tích hợp mô hình `MiniFASNetV2` phát hiện ảnh in trên giấy, video qua màn hình điện thoại/máy tính.
  - Heuristic rules: Phát hiện ảnh quá mờ (Laplacian variance), phản chiếu ánh sáng màn hình (Glare detection), kích thước khuôn mặt nhỏ.
- **Phân Tích Thuộc Tính (Face Analysis)**: Tích hợp dự đoán Tuổi, Giới tính, và Cảm xúc qua DeepFace.
- **Tối Ưu Xử Lý Cấp Thấp**: Sử dụng Eventlet cho Socket.IO, Threading riêng biệt cho luồng nhận diện, và Background Subtractor (MOG2) để bỏ qua các frame không có chuyển động (Motion Detection).

### 🖥️ Web Admin Dashboard & Kiosk Mode
- **Giao diện Glassmorphism**: Thiết kế thẻ kính mờ (frosted-glass) hiện đại, hỗ trợ hiệu ứng động bắt mắt.
- **Kiosk HUD Realtime**: Điểm danh với luồng video thời gian thực, hiển thị Bounding Box và tỉ lệ chính xác (% Similarity) thông qua Socket.IO. Cảnh báo gian lận bằng giọng nói và Popup ngay lập tức.
- **Quản Lý Phiên Điểm Danh**: Tạo phiên điểm danh theo lớp, thời gian (ca học), với khả năng khóa tự động khi hết hạn.
- **Trợ Lý AI Thông Minh (RAG Chatbot)**: Chatbot tích hợp LLM (Gemini/Ollama) kết hợp cơ sở dữ liệu vector (ChromaDB) để tự động trả lời các thông tin liên quan đến sinh viên, thống kê điểm danh, lịch học, v.v.
- **Báo Cáo Nâng Cao**: Xuất dữ liệu đa định dạng (Excel, PDF) phục vụ thống kê đào tạo.

### 📱 Flutter Mobile App (Sinh viên & Giảng viên)
- **Kiến Trúc Offline-first**: Đồng bộ dữ liệu cục bộ qua SQLite. Sinh viên có thể xem lịch sử, Giảng viên có thể mở/đóng phiên điểm danh ngay cả khi rớt mạng (hệ thống sẽ tự động đồng bộ (Sync Manager) khi có kết nối trở lại).
- **Face Authentication / Biometrics**: Đăng nhập nhanh bằng Sinh trắc học (Fingerprint/Face ID).
- **Quản Lý Phiên Từ Xa**: Admin/Giảng viên (định vị qua GPS) có quyền mở phiên điểm danh ngay trên thiết bị di động.
- **Quét Mã QR & Firebase Cloud Messaging (FCM)**: Bổ trợ điểm danh QR, nhận Push Notifications (thông báo có phiên điểm danh mới, cảnh báo gian lận).

---

## 📂 Cấu Trúc Thư Mục Hệ Thống

```text
NDKHM_DDSV_MTU/
├── app.py                  # Entry point Flask, khởi tạo Socket.IO & RAG
├── config.py               # Quản lý cấu hình toàn cục (AI Engine, Database...)
├── core/                   # Cốt lõi AI Engines
│   ├── engine.py           # Factory sinh ra các AI Model
│   ├── anti_spoofing.py    # Liveness detection (MiniFASNetV2)
│   ├── detector_yolo.py    # YOLO Face Detector
│   ├── embedder_resnet.py  # ResNet Face Embedder
│   └── camera.py           # Quản lý Webcam/IP Camera
├── db/                     # Cấu trúc CSDL (MySQL)
│   ├── schema.sql          # Bảng (sinh_vien, diem_danh, gian_lan_log, phien_diem_danh...)
│   └── migrations/         # Các script cập nhật CSDL
├── routes/                 # Routing / Controllers
│   ├── api_mobile.py       # REST API cho Flutter (bảo mật bằng JWT)
│   ├── chatbot.py          # LLM Chatbot
│   └── ...                 # Auth, Dashboard, Attendance, Classes, Export
├── services/               # Bussiness Logic Layer
│   ├── recognition_thread.py # Xử lý Realtime Face Recognition chạy ngầm
│   ├── ai_chatbot.py         # Logic giao tiếp LLM & Vector DB
│   └── fcm_service.py        # Push notification service
├── mobile_flutter/         # App di động đa nền tảng
│   ├── lib/                  # Dart code (screens, models, services, providers)
│   └── pubspec.yaml          # Dependencies
├── static/ & templates/    # Giao diện Web Admin (HTML/CSS/JS Glassmorphism)
├── docker-compose.yml      # Cấu hình triển khai container (App + MySQL)
├── scripts/                # Script tự động (auto_swagger.py...)
└── train_*.py              # Scripts huấn luyện AI (ResNet, YOLO11)
```

---

## 🚀 Hướng Dẫn Cài Đặt (Local Development)

### 1. Yêu Cầu Hệ Thống
- **Python**: 3.10 - 3.11.
- **Database**: MySQL 8.0+.
- **Flutter SDK**: Phiên bản 3.x (Nếu cần build Mobile App).

### 2. Thiết Lập Môi Trường Backend

**Bước 1:** Clone repo và thiết lập môi trường ảo
```bash
git clone https://github.com/nguyen123tu/NDKHM_DDSV_MTU.git
cd NDKHM_DDSV_MTU
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

**Bước 2:** Cài đặt các gói phụ thuộc
```bash
pip install -r requirements.txt
```

**Bước 3:** Cấu hình hệ thống `.env`
- Copy `.env.example` thành `.env`.
- Cấu hình thông số DB: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- Lựa chọn engine (`AI_ENGINE=insightface` hoặc `yolo_resnet` hoặc `deepface`).

**Bước 4:** Khởi tạo CSDL MySQL
```bash
mysql -u root -p -e "CREATE DATABASE face_attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p face_attendance_db < db/schema.sql
```

**Bước 5:** Khởi chạy Backend Server
```bash
python app.py
```
> Truy cập Web Admin Dashboard: `http://localhost:5000`

### 3. Thiết Lập Flutter Mobile App

```bash
cd mobile_flutter
flutter pub get
flutter run
```
*Lưu ý:* Hãy trỏ địa chỉ `baseUrl` trong file `lib/services/api_service.dart` về IP máy tính của bạn trong mạng LAN (vd: `http://192.168.1.xxx:5000/`). Nếu sử dụng Emulator, có thể dùng `10.0.2.2`.

---

## 🐳 Triển Khai Bằng Docker (Production)

Bạn có thể chạy toàn bộ hệ thống (Web App + MySQL) chỉ bằng một lệnh duy nhất, rất thuận tiện cho quá trình deploy lên VPS/Server.

```bash
# Đảm bảo đã cập nhật đúng mật khẩu DB trong file docker-compose.yml và .env
docker-compose up --build -d
```

> Hệ thống sẽ tự động khởi tạo database thông qua `schema.sql` nếu là lần chạy đầu tiên. Thư mục `database/` và `models/` được map dưới dạng Docker volumes để tránh mất mát dữ liệu hình ảnh cũng như não bộ AI.

---

## 📚 API Documentation (Swagger)

Hệ thống có sẵn tài liệu mô tả RESTful API sử dụng Swagger UI (Flasgger), phục vụ tích hợp Mobile App hoặc các hệ thống bên thứ 3.

- **Truy cập**: Khởi chạy server và truy cập `http://localhost:5000/apidocs`
- **Tự động sinh tài liệu**: Có thể chạy script `python scripts/auto_swagger.py` để tự động parse docstring trong thư mục `routes/` thành Swagger YAML format.

---

## 🔒 Bảo Mật & Lưu Ý Quan Trọng
- File `.env` chứa các thông tin nhạy cảm (JWT Secret, API Keys, Database Password), **tuyệt đối không** push lên Git.
- Nên thiết lập SSL/HTTPS thông qua Nginx khi public ra Internet (đặc biệt bắt buộc nếu muốn sử dụng API Camera (`getUserMedia`) trên các trình duyệt hiện đại qua đường dẫn ngoài `localhost`).
- Tính năng Chatbot RAG sử dụng tài nguyên CPU/GPU đáng kể để tạo embeddings, cân nhắc sử dụng API Gemini/NVIDIA để giảm tải xử lý local.
- Anti-Spoofing MiniFASNetV2 có thể yêu cầu hiệu năng nhất định. Nếu Kiosk bị giật lag (Drop FPS), hãy tắt thông qua biến môi trường hoặc chạy ở máy chủ cấu hình mạnh hơn.

---

**© 2024-2026 MTUFace System.** Phát triển dành cho Đồ án Tốt nghiệp.
