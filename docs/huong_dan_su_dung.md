# HƯỚNG DẪN SỬ DỤNG HỆ THỐNG MTUFACE

## Giới thiệu
MTUFace là hệ thống điểm danh thông minh bằng nhận diện khuôn mặt, được phát triển cho Trường Đại học Xây Dựng Miền Tây (MTU). Hệ thống hỗ trợ điểm danh qua Web Kiosk, Camera IP (RTSP) và ứng dụng di động Flutter.

---

## 1. Đăng nhập hệ thống Web

### 1.1. Đăng nhập Admin / Giảng viên
- Truy cập URL: `http://<server-ip>:5000/`
- Nhập tài khoản và mật khẩu (tài khoản mặc định: admin / admin123)
- Sau khi đăng nhập thành công, hệ thống chuyển đến trang Dashboard.

### 1.2. Phân quyền người dùng
- **Admin**: Toàn quyền quản lý hệ thống (quản lý sinh viên, lớp, camera, training, export, chatbot AI).
- **Teacher (Giáo viên)**: Quản lý lớp của mình, mở phiên điểm danh, xem báo cáo.
- **Student (Sinh viên)**: Đăng nhập qua Mobile App, tự điểm danh, xem lịch sử cá nhân.

---

## 2. Quản lý Sinh viên

### 2.1. Thêm sinh viên mới
1. Vào menu **Sinh viên** → **Thêm mới**
2. Điền thông tin: MSSV, Họ tên, Email, Số điện thoại, Ngày sinh, Giới tính
3. Chọn **Lớp học** từ dropdown
4. Nhấn **Lưu**

### 2.2. Chụp ảnh khuôn mặt
1. Chọn sinh viên cần chụp ảnh
2. Nhấn nút **Chụp ảnh / Capture**
3. Hệ thống sẽ mở camera và chụp ảnh (nên chụp 3-5 ảnh ở các góc độ khác nhau)
4. Ảnh được lưu vào thư mục `database/<MSSV>/` (ví dụ: `database/SV001/0.jpg`, `database/SV001/1.jpg`, ...)
5. Nhấn **Lưu** để hoàn tất

### 2.3. Import sinh viên từ Excel
1. Vào **Sinh viên** → **Import Excel**
2. Chọn file `.xlsx` theo mẫu có sẵn
3. Hệ thống sẽ tự tạo tài khoản cho từng sinh viên
4. Mật khẩu mặc định cho sinh viên đăng nhập Mobile App là `123456`

---

## 3. Huấn luyện AI (Training)

### 3.1. Training toàn bộ
1. Vào menu **Training**
2. Nhấn nút **Train All** (Huấn luyện tất cả)
3. Hệ thống sẽ:
   - Quét toàn bộ thư mục `database/` (mỗi thư mục con = 1 sinh viên)
   - Đọc tất cả ảnh `.jpg/.png` trong mỗi thư mục
   - Trích xuất embedding vector cho mỗi ảnh bằng AI Engine đang chọn
   - Tính **Average Embedding** (trung bình cộng tất cả góc độ)
   - L2 Normalize vector trung bình
   - Lưu vào file `embeddings.pkl` (nạp vào RAM cho matching realtime)
4. Theo dõi tiến độ qua thanh progress bar

### 3.2. Training từng sinh viên
- Khi thêm mới 1 sinh viên hoặc cập nhật ảnh, có thể train riêng sinh viên đó
- Dùng API `train_one(mssv)` — chỉ cập nhật vector của sinh viên đó, không ảnh hưởng người khác
- File `embeddings.pkl` sẽ được merge (cập nhật vector mới, giữ nguyên vector cũ của người khác)

### 3.3. Chọn AI Engine
Hệ thống hỗ trợ 3 AI Engine, cấu hình qua biến môi trường `AI_ENGINE`:
- **insightface** (mặc định): InsightFace buffalo_l, ArcFace 512 chiều, SCRFD detector. Chính xác >99.5%, ~20 FPS.
- **yolo_resnet**: YOLOv8 + ResNet50, vector 2048 chiều. Nhanh trong phát hiện đám đông, ~30 FPS detect.
- **deepface**: DeepFace với nhiều model con (ArcFace, Facenet512, GhostFaceNet...). Hỗ trợ anti-spoofing tích hợp.

### 3.4. Lưu ý quan trọng khi training
- Mỗi sinh viên nên có **tối thiểu 3 ảnh** ở các góc độ khác nhau (chính diện, nghiêng trái, nghiêng phải)
- Ảnh phải **rõ nét**, đủ ánh sáng, không bị che khuất khuôn mặt
- Sau khi training, hệ thống tự động lưu vector vào cả file pkl VÀ cột `face_vector` trong database MySQL (phục vụ đồng bộ offline cho Mobile App)
- Nếu đổi AI Engine → phải **train lại toàn bộ** vì mỗi engine tạo vector kích thước khác nhau

---

## 4. Điểm danh

### 4.1. Mở phiên điểm danh
1. Giảng viên vào trang **Điểm danh** (Attendance)
2. Chọn **Lớp học** cần điểm danh
3. Nhấn **Mở phiên** — hệ thống tạo bản ghi `phien_diem_danh` với `trang_thai = 1` (đang mở)
4. Cài đặt thời gian hết hạn (tùy chọn) — phiên tự đóng sau thời gian quy định

### 4.2. Điểm danh qua Kiosk Web
1. Khi phiên đang mở, hệ thống bật Camera và bắt đầu stream video
2. Sinh viên đi qua camera → hệ thống tự động:
   - **Phát hiện chuyển động** (Motion Detection) → chỉ xử lý khi có người
   - **Phát hiện khuôn mặt** (Face Detection) bằng SCRFD/YOLO/MTCNN
   - **Kiểm tra Anti-Spoofing** (chống giả mạo): kiểm tra Blur Score, Glare Ratio, Face Size
   - **Trích xuất embedding** vector từ khuôn mặt
   - **So khớp Cosine Similarity** với kho dữ liệu RAM (`embeddings.pkl`)
   - Nếu khớp (similarity > threshold 0.45) → ghi nhận điểm danh vào database
3. Kết quả hiển thị realtime trên màn hình Kiosk HUD (tên, MSSV, độ chính xác)
4. Đẩy thông báo Push Notification tới Mobile App của sinh viên

### 4.3. Điểm danh qua Mobile App
1. Sinh viên mở App → vào mục **Điểm danh**
2. Chọn lớp có phiên đang mở
3. Chụp ảnh selfie → App gửi ảnh Base64 + GPS lên server
4. Server kiểm tra:
   - **Phiên điểm danh** đang mở cho lớp đó
   - **Khung giờ** check-in (cho phép sớm 15 phút, trễ 30 phút)
   - **GPS Geofencing**: kiểm tra tọa độ sinh viên có nằm trong bán kính lớp học không
   - **Device Binding**: mỗi tài khoản chỉ đăng nhập được trên 1 thiết bị
5. Nếu hợp lệ → ghi nhận điểm danh, lưu ảnh bằng chứng

### 4.4. Đóng phiên điểm danh
- Giảng viên nhấn **Đóng phiên** khi buổi học kết thúc
- Hệ thống cập nhật `trang_thai = 0` và ghi `ket_thuc = NOW()`
- Phiên hết hạn sẽ tự động đóng nếu có cài thời gian

---

## 5. Chống gian lận (Anti-Spoofing)

### 5.1. Các biện pháp chống gian lận
| Phương pháp | Mô tả | Hiệu quả |
|---|---|---|
| **Blur Score** | Kiểm tra độ mờ bằng phương sai Laplacian | Chặn ảnh mờ/chụp từ xa |
| **Glare Ratio** | Phát hiện phản quang màn hình qua kênh V (HSV) | Chặn ảnh từ điện thoại >90% |
| **Face Size Check** | Kiểm tra kích thước khuôn mặt tối thiểu | Chặn ảnh chụp từ xa |
| **MiniFASNet v2** | Mô hình ONNX phát hiện ảnh giấy/màn hình | Phát hiện 3 loại: Thật/Ảnh in/Màn hình |
| **DeepFace Liveness** | Phát hiện khuôn mặt tĩnh (ảnh in giấy) | Chặn 100% ảnh in giấy |
| **GPS Geofencing** | Kiểm tra tọa độ GPS sinh viên | Chặn check-in từ xa (Fake GPS) |
| **Device Binding** | Ràng buộc 1 tài khoản = 1 thiết bị | Chặn chia sẻ tài khoản |

### 5.2. Log gian lận
- Mọi hành vi gian lận đều được ghi vào bảng `gian_lan_log`
- Lưu loại gian lận: Fake GPS, Spoofing, Ảnh in, Màn hình điện thoại
- Lưu ảnh bằng chứng (nếu có)
- Admin có thể xem và xử lý từ trang **Gian lận** (Fraud)

---

## 6. Quản lý Camera

### 6.1. Thêm camera
1. Vào menu **Camera** → **Thêm camera**
2. Chọn loại: USB / IP / RTSP / RTMP
3. Nhập URL hoặc index (ví dụ: `0` cho webcam, `rtsp://admin:password@192.168.1.100:554/stream1` cho IP camera)
4. Đặt tên và vị trí camera

### 6.2. Camera IP hỗ trợ
Hệ thống hỗ trợ kết nối với các camera IP qua giao thức RTSP:
- **Imou**: `rtsp://admin:<password>@<ip>:554/cam/realmonitor`
- **Ezviz**: `rtsp://admin:<password>@<ip>:554/h264/ch1/main/av_stream`
- **Hikvision**: `rtsp://admin:<password>@<ip>:554/Streaming/Channels/101`
- Hoặc bất kỳ camera nào hỗ trợ RTSP/RTMP

---

## 7. Xuất báo cáo (Export)

### 7.1. Xuất Excel
1. Vào menu **Export** → **Xuất Excel**
2. Chọn lớp, khoảng thời gian
3. Hệ thống tạo file `.xlsx` chứa danh sách điểm danh chi tiết
4. Bao gồm: MSSV, Họ tên, Ngày, Giờ vào, Trạng thái, Độ chính xác

### 7.2. Xuất PDF
- Tương tự xuất Excel nhưng định dạng PDF
- Phù hợp để in ấn hoặc nộp báo cáo

---

## 8. AI Chatbot (Trợ lý AI)

### 8.1. Truy cập Chatbot
1. Vào menu **AI Chatbot** từ sidebar
2. Chatbot sẽ hiển thị giao diện chat

### 8.2. Xây dựng Kho tri thức
- Nhấn **Build Knowledge** để quét toàn bộ dự án và lưu vào ChromaDB
- Hệ thống sẽ đọc: báo cáo đồ án, mã nguồn Python, SQL schema, cấu hình, tài liệu
- Chia nhỏ thành các chunk 800 ký tự với overlap 200 ký tự
- Index vào ChromaDB (vector database)
- Cần build lại mỗi khi có thay đổi lớn trong code/tài liệu

### 8.3. Các câu hỏi mẫu
- "Hệ thống điểm danh hoạt động như thế nào?"
- "Giải thích thuật toán ArcFace trong dự án"
- "Cấu trúc database gồm những bảng nào?"
- "Làm sao để train AI cho sinh viên mới?"
- "API mobile hỗ trợ những endpoint nào?"
- "Ngưỡng similarity threshold là gì?"
- "Hệ thống phát hiện gian lận bằng cách nào?"

### 8.4. LLM Backend
Chatbot hỗ trợ 3 LLM backend, cấu hình qua `AI_CHATBOT_LLM` trong `.env`:
- **gemini** (mặc định): Google Gemini API, miễn phí, model `gemini-2.0-flash-lite`
- **nvidia**: NVIDIA NIM API, model `meta/llama-3.1-8b-instruct`
- **ollama**: Chạy local, model `llama3` (cần cài Ollama trước)

---

## 9. Mobile App (Flutter)

### 9.1. Tính năng chính
Ứng dụng Flutter gồm 17 màn hình:
- Đăng nhập / Đăng ký
- Trang chủ Dashboard (thống kê điểm danh hôm nay)
- Điểm danh bằng khuôn mặt (selfie check-in)
- Điểm danh bằng QR Code
- Xem lịch sử điểm danh (lọc theo ngày, tháng, lớp)
- Quản lý khuôn mặt (chụp/cập nhật ảnh)
- Xem lịch học
- Thông báo Push (Firebase Cloud Messaging)
- Cài đặt tài khoản (đổi mật khẩu, thông tin cá nhân)

### 9.2. Bảo mật Mobile
- **JWT Authentication**: Mỗi request từ app phải gửi Bearer Token
- **Device Binding**: Tài khoản sinh viên chỉ đăng nhập được trên 1 thiết bị
- **Kiểm tra GPS**: Đảm bảo sinh viên có mặt tại lớp (bán kính được cấu hình cho từng lớp)
- **Ảnh bằng chứng**: Lưu ảnh selfie lúc check-in vào `database/evidence/`
- **FCM Token**: Cập nhật token Firebase để nhận thông báo push

---

## 10. Cấu hình hệ thống

### 10.1. File `.env`
Tất cả cấu hình được quản lý qua file `.env` tại thư mục gốc:
- `AI_ENGINE`: Chọn AI Engine (insightface / yolo_resnet / deepface)
- `SIMILARITY_THRESHOLD`: Ngưỡng nhận diện (mặc định 0.45, càng cao càng nghiêm ngặt)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Kết nối MySQL
- `GEMINI_API_KEY`: API key cho AI Chatbot
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: Cảnh báo qua Telegram
- `JWT_SECRET_KEY`: Khóa bí mật cho xác thực Mobile App

### 10.2. Ngưỡng Similarity Threshold
- **0.45** (mặc định): Cân bằng giữa độ chính xác và tỷ lệ nhận dạng
- **0.50-0.55**: Nghiêm ngặt hơn, ít false positive nhưng có thể bỏ sót
- **0.35-0.40**: Nới lỏng, nhận dạng dễ hơn nhưng có thể nhận nhầm
- Giảng viên có thể điều chỉnh theo môi trường thực tế (ánh sáng, camera, số lượng sinh viên)

### 10.3. Docker Deployment
Hệ thống được đóng gói bằng Docker:
```bash
docker-compose up -d
```
Bao gồm 2 container: Python Flask App + MySQL 8.0
