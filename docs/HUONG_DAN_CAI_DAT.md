# Hướng dẫn Cài đặt Hệ thống MTUFace

Hệ thống MTUFace bao gồm 2 phần: **Backend Server (Flask/Python)** và **Mobile Client (Flutter)**. Dưới đây là hướng dẫn setup môi trường trên máy Windows.

## 1. Cài đặt Backend Server (Flask)

### Bước 1: Yêu cầu môi trường
- Python 3.10 hoặc cao hơn.
- Cài đặt MS SQL Server và có tài khoản sa (Server Authentication).

### Bước 2: Cài đặt thư viện Python
Mở Terminal tại thư mục gốc của dự án (`MTUFace/NDKHM_DDSV_MTU/`) và chạy:
```bash
pip install -r requirements.txt
pip install duckduckgo-search
```
*(Lưu ý: `duckduckgo-search` bắt buộc để bot AI có chức năng duyệt web `\search`)*.

### Bước 3: Thiết lập Biến Môi Trường (File `.env`)
Tạo một file `.env` tại thư mục gốc dựa theo `.env.example`. Nội dung cần có:

```ini
# Cấu hình CSDL
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=.\SQLEXPRESS
DB_DATABASE=db_diemdanh
DB_USERNAME=sa
DB_PASSWORD=your_password

# Cấu hình AI LLM (Chọn 1 trong 3: gemini, nvidia, lmstudio)
AI_CHATBOT_LLM=lmstudio

# Nếu chọn gemini, điền API key vào đây
GEMINI_API_KEY=AIzaSy...

# Nếu chọn lmstudio (Chạy Local)
LMSTUDIO_URL=http://127.0.0.1:1234
```

### Bước 4: Tải Trọng số AI Nhận diện khuôn mặt (Weights)
- Hãy đảm bảo các file `.pt` (ví dụ `yolo11n.pt`) và thư mục `models/` đã có các file model ONNX (như Buffalo_L hoặc RetinaFace) cần thiết.

### Bước 5: Khởi động Server
```bash
python run.py
# Hoặc
python app.py
```
Nếu log báo `* Running on http://127.0.0.1:5000`, bạn đã thành công.

## 2. Cài đặt App Mobile (Flutter)

### Bước 1: Yêu cầu
- Cài đặt Flutter SDK bản mới nhất (3.x).
- Android Studio / XCode để build ra điện thoại.

### Bước 2: Build & Chạy
Truy cập vào thư mục `mobile_flutter`:
```bash
cd mobile_flutter
flutter pub get
flutter run
```
**Lưu ý Kết nối mạng**: 
- Điện thoại và Máy chủ (Laptop) **phải kết nối cùng 1 mạng Wifi**.
- Trong code Flutter (File `constants` hoặc `api_service`), phải trỏ IP về đúng IP mạng LAN của máy chủ (VD: `http://192.168.1.5:5000/api/...`). Không được để `localhost` vì điện thoại không hiểu.

## 3. Cài đặt AI Local với LM Studio (Tùy chọn)
Nếu bạn không muốn tốn tiền mua key Google Gemini, bạn có thể tự cài LM Studio để chạy AI Chatbot hoàn toàn ngắt mạng (Offline).
1. Tải phần mềm LM Studio từ trang chủ.
2. Tải một con Model nhẹ (như `Qwen 1.5` hoặc `Llama 3 8B Quantized`).
3. Bật Local Server trong LM Studio (Port mặc định `1234`).
4. Khởi động lại Flask Server của dự án. AI Chatbot sẽ tự động trỏ vào não của LM Studio.
