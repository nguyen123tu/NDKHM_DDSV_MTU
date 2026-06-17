# Đề Cương Báo Cáo Đồ Án Tốt Nghiệp — MTUFace

## Thông tin chung
- **Đề tài**: Xây dựng hệ thống điểm danh sinh viên bằng nhận diện khuôn mặt ứng dụng Deep Learning
- **Sinh viên**: Nguyễn Đông Từ
- **Trường**: Đại học Xây Dựng Miền Tây (MTU)
- **Dự kiến**: ~60 trang

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
