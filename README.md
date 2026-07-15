# 🎓 MTUFace - Hệ Thống Điểm Danh Thông Minh Ứng Dụng Trí Tuệ Nhân Tạo

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B.svg)](https://flutter.dev/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Backend-black.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

**MTUFace** là hệ thống điểm danh tự động toàn diện, được thiết kế với kiến trúc bao gồm Web Admin Dashboard và ứng dụng di động theo cơ chế "Offline-first". Dự án ứng dụng các mô hình học sâu (Deep Learning) tiên tiến nhằm tối ưu hóa quá trình nhận diện khuôn mặt, đảm bảo độ chính xác cao, thời gian phản hồi nhanh và khả năng chống gian lận hiệu quả trong môi trường học đường.

---

## 🌟 Tính Năng Nổi Bật

### 🤖 Cốt Lõi Trí Tuệ Nhân Tạo Đa Mô Hình (Multi-Engine AI Core)
- **Kiến trúc Design Pattern (Factory Method)**: Cho phép chuyển đổi linh hoạt giữa các nền tảng nhận diện AI thông qua cấu hình môi trường `.env` hoặc trực tiếp trên giao diện quản trị:
  1. **InsightFace** (`buffalo_l` / `buffalo_sc`): Đạt tốc độ suy luận vượt trội và độ chính xác ở cấp độ công nghiệp (Industrial-grade Face Verification).
  2. **YOLO11 + ResNet50**: Kết hợp phát hiện khuôn mặt tùy chỉnh với YOLO11 (tối ưu hóa bằng thuật toán MuSGD) và trích xuất đặc trưng (Embedding) thông qua mạng ResNet50.
  3. **DeepFace**: Tích hợp đa dạng các kiến trúc mạng (ArcFace, Facenet512, GhostFaceNet, v.v.).
- **Phát Hiện Thực Thể Sống & Chống Giả Mạo (Anti-Spoofing & Liveness Detection)**:
  - Tích hợp mô hình `MiniFASNetV2` giúp ngăn chặn các hành vi gian lận bằng ảnh in kỹ thuật số, video hoặc hình ảnh qua màn hình thiết bị điện tử.
  - Áp dụng các luật theo kinh nghiệm (Heuristic Rules): Phát hiện ảnh mờ (Laplacian variance), phản chiếu ánh sáng (Glare detection) và kiểm soát kích thước Bounding Box.
- **Phân Tích Thuộc Tính Khuôn Mặt (Face Analysis)**: Hỗ trợ dự đoán các thuộc tính nhân khẩu học như Tuổi, Giới tính và Trạng thái Cảm xúc thông qua framework DeepFace.
- **Tối Ưu Hiệu Suất Xử Lý**: Ứng dụng Eventlet cho kết nối Socket.IO, Threading độc lập cho luồng suy luận AI và kỹ thuật Background Subtractor (MOG2) để loại bỏ các khung hình không chứa chuyển động (Motion Detection), giúp tiết kiệm tài nguyên tính toán.

### 🖥️ Nền Tảng Quản Trị Web (Web Admin Dashboard & Kiosk Mode)
- **Giao Diện Hiện Đại (Glassmorphism)**: Ứng dụng phong cách thiết kế thẻ kính mờ, mang lại trải nghiệm người dùng (UX) hiện đại và trực quan.
- **Kiosk HUD Thời Gian Thực (Realtime Kiosk)**: Quá trình điểm danh được trực quan hóa qua luồng video trực tiếp, hiển thị Bounding Box và độ tương đồng (% Similarity) qua giao thức Socket.IO. Hệ thống cung cấp cảnh báo gian lận tức thời bằng âm thanh và thông báo (Popup).
- **Quản Lý Phiên Điểm Danh Tự Động**: Hỗ trợ khởi tạo phiên theo lớp học, ca học cùng cơ chế tự động khóa phiên khi kết thúc thời gian quy định.
- **Trợ Lý Ảo Thông Minh (RAG Chatbot)**: Ứng dụng Mô hình Ngôn ngữ Lớn (Gemini/Ollama) kết hợp cơ sở dữ liệu vector (ChromaDB) để tự động truy xuất và giải đáp thông tin liên quan đến sinh viên, thống kê điểm danh và lịch trình học tập.
- **Xuất Báo Cáo Chuyên Nghiệp**: Hỗ trợ xuất dữ liệu thống kê đa định dạng (Excel, PDF) phục vụ công tác quản lý đào tạo.

### 📱 Ứng Dụng Di Động Đa Nền Tảng (Flutter App)
- **Kiến Trúc Offline-first**: Đồng bộ hóa dữ liệu cục bộ an toàn thông qua SQLite. Giảng viên có thể thao tác quản lý phiên điểm danh ngay cả khi mất kết nối mạng. Hệ thống tự động đồng bộ hóa (Sync Manager) khi kết nối Internet được khôi phục.
- **Xác Thực Sinh Trắc Học (Biometrics Authentication)**: Hỗ trợ đăng nhập nhanh chóng thông qua vân tay hoặc Face ID.
- **Kiểm Soát Khu Vực & Quản Lý Từ Xa**: Xác thực vị trí địa lý (GPS) cho phép Giảng viên mở và quản lý phiên điểm danh trực tiếp trên thiết bị di động.
- **Bổ Trợ Quét Mã QR & Firebase Cloud Messaging (FCM)**: Đa dạng hóa phương thức điểm danh với mã QR và hệ thống thông báo đẩy (Push Notifications) cảnh báo theo thời gian thực.

---

## 📂 Kiến Trúc Mã Nguồn

```text
NDKHM_DDSV_MTU/
├── app.py                  # Entry point (Flask, Socket.IO, RAG initialization)
├── config.py               # Quản lý cấu hình toàn cục (AI Engine, Database, Security)
├── core/                   # Module lõi xử lý AI
│   ├── engine.py           # Factory Pattern khởi tạo AI Models
│   ├── anti_spoofing.py    # Liveness Detection (MiniFASNetV2)
│   ├── detector_yolo.py    # YOLO Face Detector wrapper
│   ├── embedder_resnet.py  # ResNet Feature Extraction
│   └── camera.py           # Camera/Video stream manager
├── db/                     # Quản lý cơ sở dữ liệu (MySQL)
│   ├── schema.sql          # Định nghĩa cấu trúc bảng dữ liệu
│   └── migrations/         # Database migration scripts
├── routes/                 # Controllers / RESTful API Endpoints
│   ├── api_mobile.py       # APIs dành cho Mobile App (Xác thực JWT)
│   ├── chatbot.py          # Endpoints giao tiếp LLM Chatbot
│   └── ...                 # Các module Auth, Dashboard, Attendance, Export
├── services/               # Business Logic Layer
│   ├── recognition_thread.py # Tiến trình chạy ngầm xử lý nhận diện thời gian thực
│   ├── ai_chatbot.py         # Logic tích hợp LLM & Vector DB (ChromaDB)
│   └── fcm_service.py        # Dịch vụ thông báo đẩy (FCM)
├── mobile_flutter/         # Mã nguồn ứng dụng di động (Flutter/Dart)
├── static/ & templates/    # Frontend UI (HTML/CSS/JS - Glassmorphism style)
├── docker-compose.yml      # Cấu hình triển khai containerization (App, MySQL)
├── scripts/                # Tiện ích tự động hóa (e.g., auto_swagger.py)
└── train_*.py              # Mã nguồn huấn luyện mô hình (ResNet, YOLO11)
```

---

## 🚀 Hướng Dẫn Cài Đặt (Local Development)

### 1. Yêu Cầu Môi Trường
- **Ngôn ngữ**: Python 3.10 - 3.11
- **Hệ Quản Trị CSDL**: MySQL 8.0+
- **Mobile Framework**: Flutter SDK 3.x

### 2. Triển Khai Backend Server

**Bước 1:** Nhân bản mã nguồn và khởi tạo môi trường ảo
```bash
git clone https://github.com/nguyen123tu/NDKHM_DDSV_MTU.git
cd NDKHM_DDSV_MTU
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

**Bước 2:** Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

**Bước 3:** Cấu hình biến môi trường
- Sao chép file `.env.example` thành `.env`.
- Cập nhật các thông số kết nối CSDL: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- Lựa chọn mô hình AI ưu tiên: `AI_ENGINE=insightface` (hoặc `yolo_resnet`, `deepface`).

**Bước 4:** Khởi tạo Cơ sở dữ liệu
```bash
mysql -u root -p -e "CREATE DATABASE face_attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p face_attendance_db < db/schema.sql
```

**Bước 5:** Khởi chạy Ứng dụng
```bash
python app.py
```
> Bảng điều khiển quản trị (Web Admin Dashboard) sẽ khả dụng tại: `http://localhost:5000`

### 3. Triển Khai Flutter Mobile App

```bash
cd mobile_flutter
flutter pub get
flutter run
```
*Lưu ý:* Cập nhật hằng số `baseUrl` tại `lib/services/api_service.dart` thành địa chỉ IPv4 của máy chủ trong mạng LAN (VD: `http://192.168.1.xxx:5000/`). Đối với Android Emulator, có thể sử dụng `10.0.2.2`.

---

## 🐳 Hướng Dẫn Triển Khai Production (Docker)

Để đảm bảo tính nhất quán trên các môi trường máy chủ (VPS/Server), hệ thống hỗ trợ triển khai thông qua Docker.

```bash
# Lưu ý: Cập nhật thông tin cấu hình tại docker-compose.yml và .env trước khi thực thi
docker-compose up --build -d
```

> **Cơ chế hoạt động:** Hệ thống tự động ánh xạ cấu trúc CSDL từ `schema.sql` trong lần khởi chạy đầu tiên. Dữ liệu hình ảnh và trọng số mô hình AI (model weights) được bảo toàn thông qua cấu hình Docker Volumes (`database/`, `models/`), đảm bảo không mất dữ liệu khi tái khởi động container.

---

## 📚 Tài Liệu API (Swagger Documentation)

Hệ thống cung cấp tài liệu RESTful API tiêu chuẩn thông qua giao diện Swagger UI (tích hợp Flasgger), hỗ trợ tối đa cho việc phát triển và tích hợp các ứng dụng bên thứ ba.

- **Truy cập tài liệu**: Khởi chạy server và điều hướng tới đường dẫn `http://localhost:5000/apidocs`
- **Cập nhật tài liệu tự động**: Sử dụng lệnh `python scripts/auto_swagger.py` để trích xuất tự động các docstring từ thư mục `routes/` và biên dịch sang định dạng YAML.

---

## 🔒 Yêu Cầu Bảo Mật Hệ Thống
- Tuyệt đối bảo mật tập tin `.env`. Không xuất bản file này lên các kho lưu trữ mã nguồn mở (Git), do chứa các khóa mã hóa (JWT Secret, API Keys) và thông tin đăng nhập.
- Khuyến nghị triển khai giao thức SSL/HTTPS thông qua Reverse Proxy (như Nginx) trên môi trường Production. Việc này là yêu cầu bắt buộc nhằm kích hoạt API Media Devices (`getUserMedia`) trên các trình duyệt web hiện đại khi truy cập từ xa.
- Module AI Chatbot (RAG) tiêu thụ đáng kể tài nguyên phần cứng để nội suy vector (embeddings). Cân nhắc tích hợp API từ các nhà cung cấp bên ngoài (Gemini/NVIDIA) để giảm thiểu áp lực tính toán nội bộ.
- Module phát hiện giả mạo (MiniFASNetV2) đòi hỏi hiệu năng xử lý ổn định. Trong trường hợp giao diện Kiosk gặp hiện tượng sụt giảm khung hình (FPS drop) trên các thiết bị cấu hình thấp, có thể tiến hành vô hiệu hóa tính năng này thông qua biến môi trường.

---

**© 2024-2026 MTUFace System.** Đề tài Đồ án Tốt nghiệp Kỹ sư.
