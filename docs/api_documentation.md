# Tài liệu Giao diện Lập trình Ứng dụng (API Documentation)

Dự án MTUFace cung cấp một hệ thống API mạnh mẽ, cho phép giao tiếp giữa Mobile App, Web Frontend và Hệ thống Backend Flask. Dưới đây là các API chính yếu:

## 1. API Điểm danh Nhận diện Khuôn mặt
- **URL**: `/api/mobile/attend`
- **Method**: `POST`
- **Mô tả**: Gửi khung hình từ Mobile App lên máy chủ để hệ thống bóc tách khuôn mặt, so sánh với dữ liệu đã huấn luyện để điểm danh.
- **Yêu cầu Payload (Multipart/form-data)**:
  - `image`: File ảnh `.jpg` (Khung hình chụp từ Mobile).
  - `device_id`: Mã định danh thiết bị.
  - `session_id`: (Tuỳ chọn) ID của phiên điểm danh hiện tại.
- **Luồng xử lý nội bộ**:
  1. Gửi ảnh vào module `core/detector.py` để tìm vị trí khuôn mặt. (Hỗ trợ cảnh báo chống gian lận - Spoofing).
  2. Truyền khuôn mặt sang `core/embedder.py` để tính vector 512 chiều (ArcFace).
  3. So sánh Vector này với toàn bộ sinh viên bằng `core/matcher.py`. Ngưỡng cho phép mặc định (Threshold) là `0.4` - `0.5` tuỳ môi trường sáng.
- **Kết quả trả về**:
  - `status`: `success` (Đã nhận dạng) / `error` (Không tìm thấy hoặc chưa đăng ký).
  - `student`: Thông tin sinh viên nhận diện thành công.

## 2. API Quản lý Thiết bị Mobile
- **URL**: `/api/mobile/devices`
- **Method**: `POST` / `GET`
- **Mô tả**: Quản lý thiết bị điểm danh. Ứng dụng Flutter cần đăng ký thiết bị vào hệ thống trước khi điểm danh.
- **Payload (Khi POST)**:
  - `device_name`: Tên thiết bị (VD: Pixel 7).
  - `location`: Vị trí gắn thiết bị (VD: Phòng máy tính).

## 3. API Tích hợp AI Chatbot (RAG)
Backend cung cấp các Endpoint để tương tác với AI:

### A. Non-Streaming Chatbot (Đợi trả lời 1 lần)
- **URL**: `/chatbot/ask` (Đã chuyển thành route chung trên Flask thay vì mobile riêng biệt)
- **Method**: `POST`
- **Payload (JSON)**: `{"question": "Bạn tên gì?"}`
- **Kết quả trả về (JSON)**: `{"answer": "...", "sources": [...]}`
- **Lưu ý**: Endpoint này ít được khuyên dùng do thời gian chờ đợi phản hồi từ LLM lâu.

### B. Streaming Chatbot (Trả chữ chạy mượt mà - Mặc định cho Mobile & Web)
- **URL**: `/chatbot/ask_stream`
- **Method**: `POST`
- **Mô tả**: Trả về dữ liệu kiểu `text/event-stream` (Server-Sent Events - SSE). Giải pháp này giúp hiển thị câu trả lời ngay lập tức từng chữ một như ChatGPT, hỗ trợ tốt cho giao diện Mobile Flutter và Web.

### C. Lịch sử Chat
- **URL**: `/chatbot/history`
- **Method**: `GET`
- **Mô tả**: Lấy danh sách tối đa 30 tin nhắn gần nhất từ Database (bảng `chat_message` và `chat_session`). Lịch sử được lưu vĩnh viễn theo người dùng.

## 4. WebSockets (Socket.IO) Real-time
- Dự án sử dụng Socket.IO để phát tín hiệu realtime từ Server xuống các trang Web.
- **Sự kiện chính**: `attendance_update`
- **Mô tả**: Khi một sinh viên điểm danh thành công từ API Mobile, Server lập tức phát một gói tin `attendance_update` (bao gồm Hình ảnh, Tên, MSSV). Giao diện Web (Live) sẽ nhận gói tin này và tự động cập nhật bảng xếp hạng mà không cần phải reload lại trang web (F5).
