   # CÂU HỎI THƯỜNG GẶP (FAQ) — HỆ THỐNG MTUFACE

---

## 📋 Mục lục
1. [Câu hỏi chung](#1-câu-hỏi-chung)
2. [Training & Nhận diện](#2-training--nhận-diện)
3. [Điểm danh](#3-điểm-danh)
4. [Anti-Spoofing & Gian lận](#4-anti-spoofing--gian-lận)
5. [Mobile App](#5-mobile-app)
6. [AI Chatbot](#6-ai-chatbot)
7. [Database & Cấu hình](#7-database--cấu-hình)
8. [Xử lý lỗi](#8-xử-lý-lỗi)

---

## 1. Câu hỏi chung

### Hệ thống MTUFace là gì?
MTUFace là hệ thống điểm danh thông minh sử dụng nhận diện khuôn mặt, được phát triển cho Trường Đại học Xây Dựng Miền Tây. Hệ thống sử dụng AI (InsightFace/DeepFace/YOLO) để tự động nhận diện sinh viên khi đi qua camera Kiosk hoặc khi tự chụp ảnh trên Mobile App.

### Hệ thống gồm những thành phần nào?
- **Backend**: Python Flask + SocketIO + Eventlet
- **AI Engine**: InsightFace (SCRFD + ArcFace 512d) / DeepFace / YOLO+ResNet
- **Database**: MySQL 8.0 với 8 bảng
- **Frontend Web**: HTML/CSS/JS Bootstrap 5 + Chart.js + Jinja2
- **Mobile App**: Flutter (Dart) với 17 màn hình
- **AI Chatbot**: RAG pipeline (ChromaDB + Gemini/NVIDIA/Ollama)
- **Alerts**: Telegram Bot cho cảnh báo realtime

### Độ chính xác của hệ thống bao nhiêu?
- **InsightFace (buffalo_l)**: >99.5% chính xác, ~20 FPS
- **DeepFace (ArcFace)**: >98% chính xác, 10-12 FPS
- **YOLO11+ResNet50**: Phát hiện nhanh đám đông, lên tới 30 người/frame

### Hệ thống có cần internet không?
- **Điểm danh**: Không cần internet. AI chạy local trên server.
- **AI Chatbot**: Cần internet nếu dùng Gemini hoặc NVIDIA NIM. Dùng Ollama (local) thì không cần.
- **Mobile App**: Cần kết nối mạng nội bộ (LAN/WiFi) với server.

---

## 2. Training & Nhận diện

### Làm sao để train AI cho sinh viên mới?
1. Chụp tối thiểu 3 ảnh khuôn mặt ở các góc độ khác nhau (chính diện, nghiêng trái, nghiêng phải)
2. Ảnh được lưu vào thư mục `database/<MSSV>/` (ví dụ: `database/SV001/0.jpg`)
3. Vào trang **Training** → nhấn **Train All** hoặc train riêng sinh viên đó
4. Hệ thống trích xuất embedding vector → tính trung bình → lưu vào `embeddings.pkl`

### Chụp bao nhiêu ảnh là đủ?
Tối thiểu 3 ảnh, khuyến nghị 5-10 ảnh ở các góc khác nhau. Càng nhiều góc, AI càng chính xác.

### File embeddings.pkl là gì?
Đây là file pickle chứa dictionary `{mssv: avg_embedding_vector}`. Mỗi sinh viên có 1 vector trung bình (average embedding) được L2 normalize. File này được load vào RAM để matching cực nhanh trong realtime.

### Khi nào cần train lại?
- Khi thêm sinh viên mới (có thể train riêng bằng `train_one(mssv)`)
- Khi cập nhật/thêm ảnh cho sinh viên
- Khi đổi AI Engine (bắt buộc train lại toàn bộ vì vector khác kích thước)
- Khi nhận dạng sai nhiều (có thể do ảnh cũ chất lượng kém)

### Có thể train riêng 1 sinh viên không?
Có! Sử dụng `train_one(mssv)`. Hệ thống chỉ cập nhật vector của sinh viên đó mà không ảnh hưởng các vector khác trong file pkl.

### Sự khác nhau giữa các AI Engine?
| Engine | Detector | Embedder | Vector | Ưu điểm | Nhược điểm |
|---|---|---|---|---|---|
| InsightFace | SCRFD | ArcFace | 512d | Chính xác nhất (>99.5%) | Cần ~90MB model |
| DeepFace | RetinaFace/MTCNN | ArcFace/Facenet | Tùy model | Đa dạng model, có anti-spoofing | FPS thấp hơn |
| YOLO+ResNet | YOLOv8 | ResNet50 | 2048d | Nhanh nhất, tốt với đám đông | File pkl lớn hơn |

### Similarity Threshold là gì? Nên đặt bao nhiêu?
Ngưỡng tối thiểu để xác định 2 khuôn mặt là cùng 1 người. Được tính bằng Cosine Similarity (0.0 → 1.0).
- **0.45** (mặc định): Cân bằng tốt nhất
- **0.50+**: Nghiêm ngặt hơn, giảm nhận nhầm nhưng có thể bỏ sót
- **<0.40**: Nới lỏng, dễ nhận nhầm

### Cosine Similarity hoạt động thế nào?
Cosine Similarity đo góc giữa 2 vector embedding. Công thức: `cos(θ) = dot(A, B) / (||A|| * ||B||)`. Kết quả từ -1 (ngược hướng) đến 1 (cùng hướng). Trong hệ thống, vector đã L2 normalize nên chỉ cần tính `dot(A, B)`.

---

## 3. Điểm danh

### Quy trình điểm danh tự động (Kiosk) diễn ra như thế nào?
1. Giảng viên **mở phiên** điểm danh cho lớp
2. Camera bật và stream video realtime
3. Hệ thống phát hiện chuyển động (Motion Detection) → chỉ xử lý khi có người
4. Phát hiện khuôn mặt bằng SCRFD/YOLO
5. Kiểm tra Anti-Spoofing (chống giả mạo)
6. Trích xuất embedding vector
7. So khớp với kho dữ liệu RAM bằng Cosine Similarity
8. Nếu similarity > threshold → ghi nhận điểm danh + thông báo Telegram + Push Notification

### Phiên điểm danh là gì?
Phiên (Session) là đơn vị quản lý thời gian điểm danh. Mỗi phiên thuộc 1 lớp, có trạng thái mở/đóng, có thời gian bắt đầu và kết thúc. Sinh viên chỉ điểm danh được khi phiên đang mở. Bảng `phien_diem_danh` trong database lưu thông tin phiên.

### Tại sao hệ thống chỉ có Check-in mà không có Check-out?
Hệ thống áp dụng logic "điểm danh một chiều" (Check-in only) để tối giản và tối ưu tốc độ dòng người đi qua Kiosk. Tuy nhiên Mobile App vẫn hỗ trợ checkout nếu cần.

### Có thể điểm danh nhiều lần trong ngày không?
Có thể điểm danh cho nhiều phiên khác nhau trong ngày (ví dụ: sáng buổi học Toán, chiều buổi học Lý). Tuy nhiên hệ thống có **cooldown** để tránh ghi trùng (mặc định 8 giờ giữa các lần ghi cho cùng sinh viên - cùng lớp).

### Mobile check-in hoạt động ra sao?
1. Sinh viên mở App → chọn lớp → chụp selfie
2. App gửi ảnh Base64 + tọa độ GPS + Device ID lên server
3. Server kiểm tra: phiên đang mở, khung giờ hợp lệ, GPS trong bán kính, device binding
4. Nếu OK → ghi điểm danh + lưu ảnh bằng chứng vào `database/evidence/<ngày>/`

---

## 4. Anti-Spoofing & Gian lận

### Hệ thống chống gian lận bằng cách nào?
Hệ thống sử dụng nhiều lớp bảo vệ:
1. **Blur Score** (Laplacian Variance): Chặn ảnh mờ, chụp từ xa
2. **Glare Ratio** (HSV V-channel): Phát hiện phản quang màn hình điện thoại (>90% hiệu quả)
3. **MiniFASNet v2** (ONNX model): Phân loại Người thật / Ảnh in / Màn hình (3 classes)
4. **DeepFace Liveness**: Kiểm tra ảnh tĩnh (100% chặn ảnh in giấy)
5. **GPS Geofencing**: Kiểm tra sinh viên có ở trong bán kính lớp học không
6. **Device Binding**: 1 tài khoản = 1 thiết bị duy nhất

### Log gian lận được lưu ở đâu?
Bảng `gian_lan_log` trong MySQL, bao gồm: thời gian, sinh viên, loại gian lận (Fake GPS, Spoofing, Ảnh in), chi tiết, ảnh bằng chứng, trạng thái xử lý.

### Điểm danh hộ có phát hiện được không?
Có. Hệ thống phát hiện qua:
- Anti-Spoofing AI chặn ảnh từ điện thoại/giấy
- GPS Geofencing chặn check-in từ xa
- Device Binding ngăn chia sẻ tài khoản
- Ảnh bằng chứng lưu lại mỗi lần check-in

---

## 5. Mobile App

### Mobile App hỗ trợ những tính năng gì?
App Flutter có 17 màn hình: Đăng nhập, Dashboard, Điểm danh selfie, Điểm danh QR, Xem lịch sử, Quản lý khuôn mặt, Lịch học, Thông báo Push, Đổi mật khẩu, v.v.

### Mật khẩu mặc định cho sinh viên là gì?
Mật khẩu mặc định là `123456`. Sinh viên nên đổi mật khẩu sau lần đăng nhập đầu tiên.

### Tại sao không đăng nhập được trên thiết bị mới?
Do tính năng **Device Binding** — mỗi tài khoản chỉ được đăng nhập trên 1 thiết bị. Admin cần reset cột `device_id` trong database cho sinh viên đó.

### Mobile API sử dụng xác thực gì?
**JWT (JSON Web Token)** với thuật toán HS256. Token gửi qua header `Authorization: Bearer <token>`. Token hết hạn sau 24 giờ (cấu hình qua `JWT_EXPIRE_HOURS`).

### Các API endpoint chính cho Mobile?
| Endpoint | Method | Mô tả |
|---|---|---|
| `/api/mobile/login` | POST | Đăng nhập (admin hoặc sinh viên) |
| `/api/mobile/checkin` | POST | Check-in điểm danh |
| `/api/mobile/checkout` | POST | Checkout |
| `/api/mobile/stats` | GET | Thống kê điểm danh hôm nay |
| `/api/mobile/history` | GET | Lịch sử điểm danh (filter: mssv, lop_id, date, month, year) |
| `/api/mobile/register_face` | POST | Đăng ký khuôn mặt |
| `/api/mobile/classes` | GET | Danh sách lớp học |
| `/api/mobile/profile` | GET | Thông tin cá nhân |
| `/api/mobile/change-password` | POST | Đổi mật khẩu |
| `/api/mobile/fcm-token` | POST | Cập nhật FCM token |
| `/api/mobile/attendance/<id>` | DELETE | Xóa bản ghi điểm danh (admin only) |
| `/api/mobile/attendance/clear` | DELETE | Xóa toàn bộ lịch sử (admin only) |

---

## 6. AI Chatbot

### Chatbot hoạt động dựa trên gì?
Chatbot sử dụng RAG (Retrieval-Augmented Generation):
1. **Thu thập**: Đọc mã nguồn, tài liệu, SQL schema → chia nhỏ thành chunks
2. **Embedding**: Lưu các chunk vào ChromaDB (vector database)
3. **Truy vấn**: Khi người dùng hỏi, tìm 5 chunks liên quan nhất
4. **Sinh câu trả lời**: Gửi chunks + câu hỏi cho LLM (Gemini/NVIDIA/Ollama)

### Cần build Knowledge Base khi nào?
- Lần đầu tiên sử dụng chatbot
- Sau khi thay đổi lớn trong code hoặc tài liệu
- Sau khi thêm file tài liệu mới vào `docs/`

### Chatbot có bảo mật không?
Có! System prompt quy định TUYỆT ĐỐI không tiết lộ: API key, token, mật khẩu, database credentials, đường dẫn tuyệt đối. Ngoài ra, trước khi gửi context cho LLM, hệ thống tự động lọc bỏ thông tin nhạy cảm bằng regex patterns.

### Chatbot có thể trả lời sai không?
Chatbot trả lời dựa trên kiến thức dự án trong ChromaDB, nên nếu kiến thức đầy đủ thì rất chính xác. Nếu câu hỏi ngoài phạm vi hoặc kiến thức chưa đủ, chatbot sẽ nói rõ thay vì bịa thông tin.

---

## 7. Database & Cấu hình

### Database gồm những bảng nào?
| Bảng | Mô tả |
|---|---|
| `lop_hoc` | Danh sách lớp học (mã lớp, tên, khoa, giáo viên) |
| `sinh_vien` | Thông tin sinh viên (MSSV, họ tên, avatar, face_vector, device_id) |
| `diem_danh` | Lịch sử điểm danh (sinh viên, lớp, thời gian, trạng thái, độ chính xác) |
| `camera` | Danh sách camera (USB/IP/RTSP) |
| `canh_bao` | Cảnh báo phát hiện người lạ |
| `admin` | Tài khoản quản trị (admin/teacher) |
| `thong_bao` | Thông báo cho sinh viên |
| `gian_lan_log` | Log gian lận (Fake GPS, Spoofing, Ảnh in) |
| `phien_diem_danh` | Phiên điểm danh (mở/đóng cho từng lớp) |

### Cách reset mật khẩu sinh viên?
Chạy SQL:
```sql
UPDATE sinh_vien SET password_hash = '<hash_mới>' WHERE mssv = '<MSSV>';
```
Hoặc admin reset qua giao diện web.

### Cách cài đặt thông báo Telegram?
1. Tạo Bot trên Telegram qua @BotFather → lấy Bot Token
2. Lấy Chat ID (ID nhóm hoặc cá nhân)
3. Cấu hình trong `.env`:
   - `TELEGRAM_BOT_TOKEN=<token>`
   - `TELEGRAM_CHAT_ID=<chat_id>`
4. Hệ thống sẽ tự động gửi cảnh báo khi phát hiện người lạ hoặc gian lận

---

## 8. Xử lý lỗi

### Lỗi "Không tìm thấy file não bộ: embeddings.pkl"
→ Chưa train AI. Vào trang Training → nhấn **Train All** để tạo file embeddings.pkl

### Lỗi "GEMINI_API_KEY không hợp lệ"
→ Kiểm tra API key trong file `.env`. Lấy key miễn phí tại: https://makersuite.google.com/app/apikey

### Lỗi "ModuleNotFoundError: No module named 'chromadb'"
→ Cài ChromaDB: `pip install chromadb`

### Lỗi "Token đã hết hạn" trên Mobile App
→ Token JWT hết hạn (mặc định 24h). Đăng nhập lại để lấy token mới.

### Camera không hiển thị video
→ Kiểm tra:
1. Camera có đang hoạt động không (thử mở bằng VLC nếu IP camera)
2. Index camera đúng chưa (webcam thường là 0)
3. URL RTSP đúng format chưa
4. Firewall có chặn port không

### Nhận diện sai người
→ Có thể do:
1. Ảnh training chất lượng kém → chụp lại ảnh mới và train lại
2. Ngưỡng threshold quá thấp → tăng `SIMILARITY_THRESHOLD` lên 0.50-0.55
3. Ánh sáng kém → cải thiện điều kiện ánh sáng
4. Ít ảnh training → chụp thêm ảnh ở nhiều góc

### Hệ thống chạy chậm / FPS thấp
→ Giải pháp:
1. Giảm `DET_SIZE` xuống (320, 320) thay vì (640, 640)
2. Giảm `MAX_FPS` xuống 10
3. Dùng InsightFace `buffalo_sc` (nhẹ hơn buffalo_l)
4. Nếu có GPU NVIDIA → cài `onnxruntime-gpu` và đổi provider sang CUDAExecutionProvider
