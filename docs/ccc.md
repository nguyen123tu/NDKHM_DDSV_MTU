# Đề Cương Báo Cáo Đồ Án Tốt Nghiệp — MTUFace

## Thông tin chung
- **Đề tài**: Xây dựng hệ thống điểm danh sinh viên bằng nhận diện khuôn mặt ứng dụng Deep Learning
- **Sinh viên**: Nguyễn Đông Từ
- **Trường**: Đại học Xây Dựng Miền Tây (MTU)
- **Dự kiến**: ~60 trang

---

## CẤU TRÚC TỔNG THỂ DỰ ÁN (Bản đồ hệ thống)

> Đây là toàn bộ cấu trúc thực tế của dự án, dùng làm cơ sở để viết nội dung từng chương.

```text
NDKHM_DDSV_MTU/
│
├── app.py                          # Flask Application Factory + SocketIO Entry Point
├── config.py                       # Cấu hình hệ thống (đọc .env), DevelopmentConfig/ProductionConfig
├── requirements.txt                # 37 thư viện Python (Flask, InsightFace, YOLO, PyTorch...)
├── Dockerfile                      # Docker image cho backend
├── docker-compose.yml              # Compose: Flask App + MySQL 8.0
├── .env / .env.example             # Biến môi trường (DB, AI engine, API keys...)
├── serviceAccountKey.json          # Firebase Admin SDK key
├── yolo11n.pt                      # Model YOLO11 pretrained (~5.6MB)
├── train_yolo11.py                 # Script huấn luyện YOLO11 custom
├── train_resnet_face.py            # Script huấn luyện ResNet50 trên face dataset
│
├── core/                           # ═══ AI CORE ENGINE ═══
│   ├── engine.py                   # Factory Pattern: chọn InsightFace / YOLO+ResNet / DeepFace
│   ├── detector.py                 # Face Detector — InsightFace (SCRFD)
│   ├── detector_yolo.py            # Face Detector — YOLO11 (GPU/CPU, warmup, conf=0.5)
│   ├── embedder.py                 # Face Embedder — InsightFace (ArcFace 512d)
│   ├── embedder_resnet.py          # Face Embedder — ResNet50 pretrained ImageNet (2048d)
│   ├── matcher.py                  # Face Matcher — Cosine Similarity, hot-reload pkl
│   ├── trainer.py                  # Face Trainer — quét ảnh → avg embedding → pkl
│   ├── camera.py                   # Camera Manager — USB/IP/RTSP, ThreadedCamera, multi-cam
│   └── anti_spoofing.py            # Anti-Spoofing — MiniFASNetV2 ONNX (Real/Fake/Screen)
│
├── db/                             # ═══ DATABASE LAYER ═══
│   ├── connection.py               # MySQL Connection Pool (pool_size=5), execute_query/update/one
│   ├── schema.sql                  # 9 bảng: lop_hoc, sinh_vien, diem_danh, camera, canh_bao,
│   │                               #         admin, thong_bao, gian_lan_log, phien_diem_danh
│   ├── seed.sql                    # Dữ liệu mẫu
│   └── migrations/                 # SQL migrations (add_phien_diem_danh...)
│
├── services/                       # ═══ BUSINESS LOGIC LAYER ═══
│   ├── recognition_thread.py       # Luồng nhận diện realtime (Motion→Detect→Embed→Match→Log)
│   ├── attendance_service.py       # Nghiệp vụ điểm danh: log, history, thống kê, đa phiên
│   ├── student_service.py          # Nghiệp vụ sinh viên: CRUD, avatar, tìm kiếm
│   ├── class_service.py            # Nghiệp vụ lớp học: CRUD, danh sách, thống kê
│   ├── export_service.py           # Xuất Excel/PDF: điểm danh ngày, ma trận tháng, roster
│   ├── ai_chatbot.py              # AI Chatbot RAG: Gemini / NVIDIA NIM / Ollama
│   ├── knowledge_builder.py        # Xây dựng ChromaDB knowledge base từ source code
│   ├── fcm_service.py              # Firebase Cloud Messaging — Push Notification
│   └── telegram_alert.py           # Telegram Bot — gửi tin nhắn + ảnh cảnh báo
│
├── routes/                         # ═══ CONTROLLERS (Flask Blueprints) ═══
│   ├── __init__.py                 # Đăng ký tất cả Blueprints
│   ├── auth.py                     # Đăng nhập / Xác thực admin
│   ├── dashboard.py                # Trang chủ Admin Dashboard
│   ├── students.py                 # CRUD sinh viên + duyệt khuôn mặt
│   ├── classes.py                  # CRUD lớp học + lịch học
│   ├── attendance.py               # Điểm danh live + lịch sử
│   ├── training.py                 # Huấn luyện AI + chuyển đổi engine
│   ├── camera_mgmt.py              # Quản lý camera IP/USB
│   ├── export.py                   # Xuất báo cáo Excel/PDF
│   ├── public.py                   # Trang công khai: selfcheck, tra cứu, API recognize
│   ├── chatbot.py                  # AI Chatbot endpoint
│   ├── fraud.py                    # Cảnh báo gian lận
│   ├── support.py                  # Yêu cầu hỗ trợ (Ticket)
│   └── api_mobile.py              # RESTful API cho Flutter App (82KB, JWT Auth)
│
├── templates/                      # ═══ GIAO DIỆN WEB (Jinja2) ═══
│   ├── base.html                   # Layout chính (sidebar, navbar, glassmorphism)
│   ├── auth/                       # Trang đăng nhập
│   ├── dashboard/
│   │   ├── index.html              # Dashboard chính (thống kê, biểu đồ Chart.js)
│   │   ├── kiosk.html              # Kiosk HUD (camera realtime + audio feedback)
│   │   ├── fraud_alerts.html       # Cảnh báo gian lận
│   │   └── support.html            # Yêu cầu hỗ trợ
│   ├── students/
│   │   ├── list.html               # Danh sách sinh viên
│   │   ├── add.html / edit.html    # Thêm / sửa sinh viên
│   │   ├── detail.html             # Chi tiết sinh viên
│   │   └── pending.html            # Duyệt đăng ký khuôn mặt
│   ├── classes/
│   │   ├── list.html / add.html / edit.html / detail.html
│   │   └── schedule.html           # Lịch học
│   ├── attendance/
│   │   ├── live.html               # Điểm danh trực tiếp (WebSocket SocketIO)
│   │   └── history.html            # Lịch sử điểm danh
│   ├── training/
│   │   ├── index.html              # Huấn luyện AI (progress bar realtime)
│   │   └── capture.html            # Chụp ảnh đăng ký khuôn mặt
│   ├── chatbot/chat.html           # Giao diện AI Chatbot
│   ├── export/index.html           # Xuất báo cáo Excel/PDF
│   ├── public/
│   │   ├── selfcheck.html          # Self-check không đăng nhập
│   │   └── attendance_public.html  # Tra cứu điểm danh công khai
│   └── errors/error.html           # Trang lỗi 404/500/403/405
│
├── static/                         # ═══ ASSETS TĨNH ═══
│   ├── css/
│   │   ├── main.css                # Design system chung (22KB)
│   │   ├── glassmorphism.css       # Hiệu ứng kính mờ
│   │   ├── dashboard.css
│   │   ├── components/             # ai_assistant.css, voice_chat.css
│   │   └── pages/                  # 17 file CSS riêng từng trang
│   ├── js/
│   │   ├── attendance_realtime.js  # SocketIO realtime client
│   │   ├── charts.js               # Chart.js biểu đồ
│   │   ├── components/             # ai_assistant.js, voice_engine.js
│   │   └── pages/                  # 18 file JS riêng từng trang
│   ├── img/                        # Logo, favicon, hình ảnh
│   └── uploads/                    # File upload từ người dùng
│
├── database/                       # ═══ DỮ LIỆU KHUÔN MẶT ═══
│   ├── {MSSV}/                     # Thư mục ảnh mỗi sinh viên (VD: 23D14801030050/)
│   │   ├── 0.jpg, 1.jpg...         # Ảnh khuôn mặt nhiều góc độ
│   └── evidence/                   # Ảnh bằng chứng điểm danh
│
├── models/                         # ═══ AI MODELS ═══
│   ├── embeddings.pkl              # Não bộ InsightFace (mssv → vector 512d)
│   ├── embeddings_yolo_resnet.pkl  # Não bộ YOLO+ResNet (mssv → vector 2048d)
│   ├── MiniFASNetV2.onnx           # Anti-spoofing model (1.7MB)
│   ├── yolov8n-face.pt             # YOLO face detector (6.2MB)
│   ├── haarcascade_frontalface_default.xml
│   ├── chroma_db/                  # ChromaDB knowledge base cho AI Chatbot
│   └── knowledge_status.json       # Trạng thái kho tri thức
│
├── mobile_flutter/                 # ═══ FLUTTER MOBILE APP ═══
│   ├── lib/
│   │   ├── main.dart               # Entry point + Firebase init
│   │   ├── models/                 # Data models
│   │   │   ├── user_model.dart
│   │   │   ├── attendance_record.dart
│   │   │   └── session_model.dart
│   │   ├── providers/              # State management
│   │   │   ├── auth_provider.dart
│   │   │   ├── attendance_provider.dart
│   │   │   └── connectivity_provider.dart
│   │   ├── services/               # Business logic
│   │   │   ├── api_service.dart         # REST API client (19KB)
│   │   │   ├── sync_manager.dart        # Offline-first sync (10KB)
│   │   │   ├── offline_queue_service.dart
│   │   │   ├── export_service.dart
│   │   │   ├── firebase_messaging_service.dart
│   │   │   └── face_recognition_service.dart
│   │   ├── screens/                # 19 màn hình
│   │   │   ├── login_screen.dart / register_screen.dart / onboarding_screen.dart
│   │   │   ├── home_screen.dart (27KB) / profile_screen.dart
│   │   │   ├── student_attendance_screen.dart / session_history_screen.dart
│   │   │   ├── scan_screen.dart / student_qr_scanner_screen.dart
│   │   │   ├── admin_session_screen.dart / admin_session_detail_screen.dart
│   │   │   ├── admin_stats_screen.dart / face_approval_screen.dart
│   │   │   ├── chatbot_screen.dart (27KB)
│   │   │   ├── notifications_screen.dart / schedule_screen.dart
│   │   │   ├── history_report_screen.dart / sync_status_screen.dart
│   │   │   └── device_settings_screen.dart
│   │   ├── theme/app_theme.dart    # Material theme
│   │   └── data/                   # SQLite local database
│   ├── android/ / ios/             # Platform-specific
│   └── pubspec.yaml                # Dependencies
│
├── tools/                          # ═══ CÔNG CỤ HỖ TRỢ ═══
│   ├── convert_onnx_to_tflite.py   # Chuyển đổi model cho mobile
│   └── download_models.py          # Tải model AI
│
├── scripts/                        # ═══ SCRIPTS ═══
│   ├── auto_swagger.py             # Tự động tạo Swagger API docs
│   └── fix_duplicates.py           # Sửa dữ liệu trùng
│
└── docs/                           # ═══ TÀI LIỆU ═══
    ├── bao_cao_do_an.md            # Báo cáo đồ án (bản MD)
    ├── api_documentation.md        # API docs
    ├── huong_dan_su_dung.md        # Hướng dẫn sử dụng
    ├── faq.md                      # Câu hỏi thường gặp
    └── PROJECT_STRUCTURE.md        # Cấu trúc dự án
```

### Tổng kết số lượng

| Thành phần | Số lượng | Ghi chú |
|---|---|---|
| **Python modules** | ~35 files | Backend + AI |
| **HTML templates** | ~25 files | Jinja2 (Glassmorphism) |
| **CSS files** | ~22 files | Design system + pages |
| **JavaScript files** | ~22 files | Realtime + interactivity |
| **Flutter Dart files** | ~30 files | Mobile app |
| **SQL files** | 3 files | Schema + seed + migration |
| **AI Models** | 5 files | InsightFace, YOLO, Anti-spoof |
| **Tổng dòng code ước tính** | ~15,000+ | Python + Dart + JS + HTML + CSS |

### Sơ đồ kiến trúc 3 tầng

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   Web Admin       │  │  Kiosk HUD       │  │ Flutter App  │  │
│  │  (Jinja2+BS5)     │  │  (SocketIO)      │  │ (19 screens) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │
├───────────┼─────────────────────┼────────────────────┼──────────┤
│           │        BUSINESS LOGIC LAYER              │          │
│  ┌────────▼─────────────────────▼────────────────────▼───────┐  │
│  │  Flask Blueprints (14 routes) + Services (9 modules)      │  │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐ │  │
│  │  │attendance│ │recognition│ │ export   │ │  ai_chatbot │ │  │
│  │  │_service  │ │_thread    │ │_service  │ │  (RAG)      │ │  │
│  │  └──────────┘ └───────────┘ └──────────┘ └─────────────┘ │  │
│  └────────┬──────────────────────────────────────────────────┘  │
├───────────┼─────────────────────────────────────────────────────┤
│           │              AI CORE ENGINE                          │
│  ┌────────▼──────────────────────────────────────────────────┐  │
│  │  Engine Factory (Singleton + Factory Pattern)              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐ │  │
│  │  │InsightFace │  │YOLO11      │  │Anti-Spoofing         │ │  │
│  │  │SCRFD+ArcFace│ │+ResNet50   │  │MiniFASNetV2          │ │  │
│  │  │(512d)      │  │(2048d)     │  │(Real/Fake/Screen)    │ │  │
│  │  └────────────┘  └────────────┘  └──────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      DATA LAYER                                 │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌───────────┐  │
│  │MySQL 8.0 │  │embeddings.pkl│  │ChromaDB   │  │Firebase   │  │
│  │(9 bảng)  │  │(Não bộ AI)   │  │(Knowledge)│  │(FCM+Auth) │  │
│  └──────────┘  └──────────────┘  └───────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline AI Nhận diện Khuôn mặt

```
Camera Frame → Motion Detection → Face Detection → Face Embedding → Cosine Match → Log Attendance
     │              │                   │                │               │              │
     ▼              ▼                   ▼                ▼               ▼              ▼
  camera.py    MOG2 (OpenCV)     YOLO11/SCRFD      ResNet50/ArcFace   matcher.py   attendance
  USB/IP/RTSP  threshold=3000    conf=0.5           512d/2048d        threshold=0.45 _service
               skip nếu ko       bbox+crop          L2 normalize      Cosine Sim    +FCM+Telegram
               có chuyển động     +confidence        +embedding        best match
                                       │
                                       ▼
                                 Anti-Spoofing
                                 MiniFASNetV2
                                 blur/glare/size
```

---

## Cấu trúc đề cương chi tiết

### PHẦN MỞ ĐẦU (~5 trang)

#### 1. Lời mở đầu (1 trang)
- Lý do chọn đề tài, bối cảnh chuyển đổi số trong giáo dục

#### 2. Mục tiêu đề tài (1 trang)
- Mục tiêu tổng quát và cụ thể
- Phạm vi nghiên cứu

#### 3. Đối tượng và phạm vi (1 trang)
- Đối tượng: sinh viên, giảng viên, quản trị viên
- Phạm vi: trong trường MTU

#### 4. Phương pháp nghiên cứu (1 trang)
- Phương pháp phân tích thiết kế hệ thống
- Phương pháp thực nghiệm (Deep Learning)

#### 5. Bố cục báo cáo (1 trang)

---

### CHƯƠNG 1: TỔNG QUAN (~8 trang)

#### 1.1 Giới thiệu bài toán điểm danh (2 trang)
- Thực trạng điểm danh truyền thống
- Hạn chế: gian lận, tốn thời gian, thiếu chính xác

#### 1.2 Tổng quan về nhận diện khuôn mặt (3 trang)
- Lịch sử phát triển Face Recognition
- Các phương pháp: truyền thống (Haar Cascade, HOG) vs Deep Learning
- Ứng dụng thực tế

#### 1.3 Các công trình liên quan (2 trang)
- Nghiên cứu trong và ngoài nước
- So sánh ưu nhược điểm

#### 1.4 Đề xuất giải pháp (1 trang)
- Tổng quan giải pháp MTUFace

---

### CHƯƠNG 2: CƠ SỞ LÝ THUYẾT (~10 trang)

#### 2.1 Mạng nơ-ron tích chập CNN (2 trang)
- Kiến trúc CNN: Convolution, Pooling, Fully Connected
- Ứng dụng trong xử lý ảnh

#### 2.2 Kiến trúc ResNet50 (2 trang)
- Residual Learning, Skip Connection
- Feature extraction 2048 chiều
- Transfer Learning từ ImageNet

#### 2.3 YOLO — Phát hiện đối tượng (2 trang)
- Kiến trúc YOLOv11
- One-stage detection
- Ứng dụng phát hiện khuôn mặt

#### 2.4 InsightFace — ArcFace (2 trang)
- SCRFD (Sample and Computation Redistribution for Face Detection)
- ArcFace Loss: Additive Angular Margin
- Embedding vector 512 chiều

#### 2.5 Cosine Similarity (1 trang)
- Công thức tính độ tương đồng
- Ngưỡng nhận diện (threshold)

#### 2.6 Anti-Spoofing — Chống giả mạo (1 trang)
- MiniFASNet: phân loại Real/Fake
- Heuristic checks: blur, glare, face size

---

### CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG (~12 trang)

#### 3.1 Phân tích yêu cầu (2 trang)
- Yêu cầu chức năng (Functional Requirements)
- Yêu cầu phi chức năng (Non-functional Requirements)

#### 3.2 Kiến trúc hệ thống (2 trang)
- Kiến trúc tổng thể 3 thành phần: Web Admin + AI Core + Mobile App
- Mô hình MVC (Flask Blueprints)
- Sơ đồ kiến trúc tổng quan

#### 3.3 Thiết kế cơ sở dữ liệu (3 trang)
- Sơ đồ ERD (9 bảng: lop_hoc, sinh_vien, diem_danh, camera, canh_bao, admin, thong_bao, gian_lan_log, phien_diem_danh)
- Mô tả chi tiết từng bảng
- Quan hệ và ràng buộc (Foreign Key)

#### 3.4 Thiết kế pipeline AI (2 trang)
- Factory Pattern cho đa engine
- Pipeline: Camera → Detect → Embed → Match → Log
- Singleton Pattern cho model loading

#### 3.5 Sơ đồ Use Case (1.5 trang)
- Actor: Admin, Sinh viên, Hệ thống AI
- Các use case chính

#### 3.6 Sơ đồ hoạt động (Activity Diagram) (1.5 trang)
- Luồng điểm danh realtime
- Luồng huấn luyện AI

---

### CHƯƠNG 4: TRIỂN KHAI HỆ THỐNG (~15 trang)

#### 4.1 Công nghệ sử dụng (2 trang)
| Thành phần | Công nghệ |
|---|---|
| Backend | Python Flask + SocketIO + Eventlet |
| Database | MySQL 8.0 + Connection Pool |
| AI Engine | InsightFace / YOLO11 + ResNet50 |
| Frontend Web | Bootstrap 5 + Chart.js + Jinja2 |
| Mobile | Flutter (Dart) |
| Realtime | WebSocket (SocketIO) |
| Notification | Firebase Cloud Messaging + Telegram Bot |
| AI Chatbot | RAG (ChromaDB + Gemini API) |
| Deployment | Docker + Docker Compose |

#### 4.2 Module AI Core (3 trang)
- `engine.py`: Factory Pattern chọn engine
- `detector_yolo.py`: Phát hiện khuôn mặt bằng YOLO11
- `embedder_resnet.py`: Trích xuất embedding 2048d
- `matcher.py`: So khớp Cosine Similarity
- `trainer.py`: Huấn luyện (quét ảnh → embedding trung bình → pkl)
- `anti_spoofing.py`: MiniFASNetV2 ONNX
- `camera.py`: Quản lý đa camera (USB, IP, RTSP)

#### 4.3 Module Điểm danh Realtime (2 trang)
- `recognition_thread.py`: Background thread nhận diện
- Motion Detection (BackgroundSubtractorMOG2)
- Temporal Smoothing (4 frame xác nhận)
- Liveness Check (blur, glare, face size)
- Frame skipping tối ưu hiệu năng

#### 4.4 Module Web Admin Dashboard (2 trang)
- Giao diện Glassmorphism, dark theme
- Kiosk HUD: Audio feedback, camera tracking
- Quản lý sinh viên, lớp học, điểm danh
- Xuất báo cáo Excel/PDF
- AI Chatbot hỗ trợ

#### 4.5 Module Mobile App — Flutter (2 trang)
- Kiến trúc Offline-first (SQLite + SyncManager)
- 19 màn hình chính
- Đăng ký khuôn mặt, tra cứu điểm danh
- Push Notification (FCM)
- QR Scanner

#### 4.6 Module Hỗ trợ (2 trang)
- AI Chatbot (RAG Pipeline: ChromaDB + Gemini/NVIDIA/Ollama)
- Hệ thống cảnh báo gian lận
- Telegram Bot Alert
- Xuất báo cáo Excel/PDF (openpyxl, reportlab)

#### 4.7 Triển khai Docker (2 trang)
- Dockerfile, docker-compose.yml
- Cấu hình Production (Gunicorn/Nginx)

---

### CHƯƠNG 5: KIỂM THỬ VÀ ĐÁNH GIÁ (~6 trang)

#### 5.1 Kiểm thử chức năng (2 trang)
- Test đăng nhập, quản lý sinh viên
- Test điểm danh realtime
- Test xuất báo cáo
- Test mobile app

#### 5.2 Đánh giá hiệu năng AI (2 trang)
- Accuracy, Precision, Recall
- So sánh InsightFace vs YOLO+ResNet
- Thời gian xử lý (FPS)
- Ngưỡng threshold tối ưu

#### 5.3 Đánh giá Anti-Spoofing (1 trang)
- Test với ảnh in, video, màn hình điện thoại

#### 5.4 Giao diện người dùng (1 trang)
- Screenshot các trang chính
- Trải nghiệm người dùng

---

### PHẦN KẾT LUẬN (~4 trang)

#### 1. Kết quả đạt được (2 trang)
- Tóm tắt các chức năng đã hoàn thành
- Đóng góp của đề tài

#### 2. Hạn chế (1 trang)
- Giới hạn phần cứng, mạng
- Chưa hỗ trợ đa camera đồng thời quy mô lớn

#### 3. Hướng phát triển (1 trang)
- Tích hợp Edge AI (Raspberry Pi, Jetson Nano)
- Mở rộng anti-spoofing 3D
- Tích hợp blockchain cho xác thực

---

### PHỤ LỤC
- Tài liệu tham khảo
- Hướng dẫn cài đặt
- Mã nguồn quan trọng
- Danh sách API endpoints

---

## Open Questions

> [!IMPORTANT]
> 1. **Tên đề tài chính xác** mà bạn đã đăng ký với trường là gì?
> 2. **Tên giảng viên hướng dẫn** để ghi vào trang bìa?
> 3. **Khoa / Ngành** cụ thể (VD: Công nghệ Thông tin)?
> 4. Bạn muốn tôi bắt đầu viết từ **chương nào trước**?
> 5. Bạn có **mẫu format** (font, cỡ chữ, lề) mà trường yêu cầu không?
