# Báo Cáo Đồ Án: Điểm Danh Thông Minh Bằng Nhận Diện Khuôn Mặt (MTUFace)

## 1. Giới thiệu Tổng quan
Dự án **MTUFace** ra đời nhằm giải quyết vấn đề điểm danh thủ công tốn thời gian tại các trường đại học/cao đẳng. Bằng cách ứng dụng trí tuệ nhân tạo (Computer Vision) kết hợp ứng dụng di động (Flutter), hệ thống cho phép sinh viên điểm danh nhanh chóng, chính xác và chống gian lận.

## 2. Kiến trúc Hệ thống (System Architecture)
Hệ thống được thiết kế theo mô hình Client-Server:
- **Client (Mobile App)**: Viết bằng Flutter, thiết kế UI/UX theo xu hướng Neumorphism (3D Card). Ứng dụng quét luồng video từ camera, trích xuất khung hình và gửi lên máy chủ qua REST API (đường dẫn `/api/mobile/attend`).
- **Server (Backend)**: Viết bằng Python Flask. Đảm nhận nhiệm vụ nhận ảnh, xử lý AI, đối chiếu dữ liệu SQL Server, và phát sóng (broadcast) kết quả lên bảng xếp hạng bằng công nghệ WebSockets (Socket.IO).
- **Web Admin**: Giao diện quản trị viết bằng HTML/JS/CSS thuần, sử dụng Jinja2 Template, cho phép giảng viên tạo lớp, thêm sinh viên, cấu hình camera, xem báo cáo vắng mặt và giao tiếp với trợ lý ảo (AI Chatbot).

## 3. Lõi Công nghệ Nhận Diện (Core AI Engine)
Thư mục `core/` chứa bộ máy AI mạnh mẽ nhất của hệ thống:
1. **Face Detection (Phát hiện mặt)**: Sử dụng các mô hình gọn nhẹ (YOLO/RetinaFace) để khoanh vùng vị trí khuôn mặt trong khung hình camera gửi lên. Tích hợp các module Liveness Detection (đang thử nghiệm) để chống gian lận lấy ảnh 2D đưa vào camera.
2. **Face Embedding (Đặc trưng hóa)**: Vùng khuôn mặt được đưa qua mô hình học sâu `InsightFace` (kiến trúc ArcFace, chạy bằng ONNX Runtime) để biến đổi thành một vector 512 chiều.
3. **Face Matching (So khớp)**: So sánh khoảng cách (Cosine Distance) giữa vector chụp được và vector gốc trong CSDL. Nếu khoảng cách dưới Threshold (ngưỡng 0.45), hệ thống xác nhận danh tính thành công.

## 4. Công nghệ AI Trợ Lý Ảo (Chatbot & RAG)
Đây là một tính năng đột phá của MTUFace.
- Hệ thống nhúng một chatbot AI có thể trả lời mọi thắc mắc của giảng viên và sinh viên về điểm danh.
- **RAG (Retrieval-Augmented Generation)**: Chatbot không chém gió! Khi có câu hỏi, hệ thống dùng `knowledge_builder.py` để tra cứu trong kho tài liệu ChromaDB, lấy ra các quy chế, hướng dẫn, sau đó nhồi vào Context cho AI đọc.
- **Hỗ trợ 3 nền tảng LLM**: 
  - `gemini` (Google)
  - `nvidia`
  - `lmstudio` (Dành cho việc chạy Model nội bộ không cần mạng).
- **Tính năng lướt mạng (`/search`)**: Dù là mô hình Local AI (LM Studio), hệ thống vẫn có khả năng tự động cào tin tức từ DuckDuckGo để trả lời các câu hỏi về thời tiết, tin tức mới nhất nếu câu hỏi bắt đầu bằng chữ `/search`.

## 5. Kết luận
MTUFace không chỉ là một ứng dụng điểm danh thông thường, mà là một hệ sinh thái kết hợp hoàn hảo giữa App Mobile, Web Admin Real-time, Computer Vision và AI Chatbot/LLM tiên tiến nhất.
