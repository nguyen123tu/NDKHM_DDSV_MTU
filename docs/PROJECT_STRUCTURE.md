# Cấu trúc Dự án (Project Structure)

Dự án **MTUFace** (Điểm danh khuôn mặt thông minh) được tổ chức theo kiến trúc **Client-Server**, đảm bảo khả năng bảo trì, mở rộng và tích hợp dễ dàng các công nghệ AI. Dưới đây là phân tích chi tiết về cấu trúc các thư mục và tập tin quan trọng.

## 1. Thư mục gốc (Root Directory)

- `app.py`: Trái tim của ứng dụng Flask. Chứa hàm `create_app()`, khởi tạo SocketIO, kết nối cơ sở dữ liệu, và đăng ký các Blueprints (Routes).
- `run_server.py`: Script chạy ứng dụng chính trong môi trường Development (hỗ trợ tự động reload).
- `config.py`: Đọc các cấu hình hệ thống từ file `.env` và cung cấp một object `Config` thống nhất cho toàn bộ dự án.
- `.env`: (Không upload lên git) Chứa các biến môi trường nhạy cảm như `DB_PASSWORD`, `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `LMSTUDIO_URL`...

## 2. Server (Backend - Flask)

- `routes/`: Nơi chứa các API endpoints (Blueprints).
  - `admin.py`: Các trang quản trị trên nền Web (Dashboard, Sinh viên, Lớp học).
  - `api_mobile.py`: Các API giao tiếp chuyên biệt cho Mobile App (Flutter).
  - `chatbot.py`: API xử lý tin nhắn của AI Chatbot, bao gồm `/ask` và `/ask_stream`.
- `services/`: Lớp chứa Logic nghiệp vụ (Business Logic), giúp giảm tải cho Routes.
  - `ai_chatbot.py`: Xử lý giao tiếp với LLM (Gemini, LM Studio), quản lý Context RAG, xử lý tính năng `/search` lấy dữ liệu DuckDuckGo.
  - `knowledge_builder.py`: Module đọc các file `.md` và đưa vào ChromaDB để AI học.
  - `attendance_service.py`: Xử lý luồng nghiệp vụ khi sinh viên điểm danh (kiểm tra khoảng cách, gọi engine AI, lưu CSDL).
- `core/`: Lõi công nghệ AI Nhận diện.
  - `engine.py`, `detector.py`, `embedder.py`, `matcher.py`: Xử lý ảnh, trích xuất đặc trưng khuôn mặt (InsightFace/ArcFace) và tính toán khoảng cách vector để xác định danh tính.
- `db/`: 
  - `connection.py`: Quản lý Pool kết nối đến MS SQL Server, cung cấp các hàm `execute_query` và `execute_one`.
  - `schema.sql` / `seed.sql`: Các file thiết kế CSDL và dữ liệu mẫu.

## 3. Client & Giao diện

- `mobile_flutter/`: Chứa toàn bộ source code của Ứng dụng Di động bằng Flutter.
  - Được thiết kế bằng Neu-morphism (Giao diện thẻ 3D).
  - Giao tiếp với Server qua REST API (`routes/api_mobile.py`).
- `templates/`: Các file HTML cho Web Admin (sử dụng Jinja2).
- `static/`: Tài nguyên frontend (CSS, JS, Hình ảnh). 
  - `js/pages/chatbot_chat.js`: Quản lý giao diện chat và đọc dữ liệu Stream (Server-Sent Events) từ AI Chatbot.

## 4. Dữ liệu & AI Models

- `database/`: Chứa hình ảnh dataset mẫu của sinh viên để huấn luyện AI, cùng với thư mục ảnh chụp điểm danh thực tế (hình ảnh làm bằng chứng).
- `models/`: Chứa các trọng số AI (như YOLO, InsightFace ONNX) và `chroma_db` (Kho tri thức Vector DB cho Chatbot RAG).
- `docs/`: Chứa toàn bộ tài liệu Markdown (.md) cho dự án. Đây là nguồn kiến thức chính mà AI Chatbot sẽ học để tư vấn cho người dùng!

## 5. Hướng phát triển trong tương lai
- Tách rời Core AI thành một Microservice riêng biệt (sử dụng FastAPI) để tăng hiệu năng xử lý nhận diện song song.
- Đưa hình ảnh lưu trữ lên dịch vụ Object Storage như AWS S3 / MinIO thay vì lưu ở ổ cứng cục bộ.
