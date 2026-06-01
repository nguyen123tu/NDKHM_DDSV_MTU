# TÀI LIỆU API — HỆ THỐNG MTUFACE

## Tổng quan
Hệ thống MTUFace cung cấp 2 loại API:
1. **Web Routes**: Giao diện HTML cho dashboard quản lý (Jinja2 templates)
2. **Mobile API (REST)**: JSON API cho ứng dụng Flutter, prefix `/api/mobile`

Tất cả Mobile API yêu cầu **JWT Bearer Token** (trừ `/login` và `/register_face`).

---

## 1. Mobile API — Xác thực

### POST `/api/mobile/login`
Đăng nhập cho cả Admin và Sinh viên.

**Request Body:**
```json
{
  "username": "admin hoặc MSSV",
  "password": "mật khẩu",
  "device_id": "unique_device_identifier (bắt buộc cho sinh viên)"
}
```

**Response thành công (200):**
```json
{
  "success": true,
  "message": "Đăng nhập Admin/Sinh viên thành công",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in_hours": 24,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin | student",
    "name": "Nguyễn Văn A"
  }
}
```

**Lỗi (401):**
```json
{"success": false, "message": "Sai tài khoản hoặc mật khẩu"}
```

**Lỗi Device Binding (403):**
```json
{"success": false, "message": "Tài khoản đã được đăng nhập trên một thiết bị khác"}
```

**Cơ chế xác thực:**
- Hệ thống kiểm tra bảng `admin` trước, sau đó bảng `sinh_vien`
- JWT payload chứa: `sub` (user_id), `username`, `role`, `exp`, `iat`
- Thuật toán: HS256 với `JWT_SECRET_KEY` từ config
- Token hết hạn: 24 giờ (cấu hình qua `JWT_EXPIRE_HOURS`)
- Sinh viên bắt buộc gửi `device_id`: lần đầu tự bind, lần sau phải khớp

---

## 2. Mobile API — Điểm danh

### POST `/api/mobile/checkin`
Check-in điểm danh từ Mobile App.

**Headers:** `Authorization: Bearer <token>`

**Request Body (JSON hoặc multipart/form-data):**
```json
{
  "mssv": "SV001",
  "lop_id": 1,
  "session_id": 5,
  "do_chinh_xac": 0.95,
  "camera_id": 0,
  "trang_thai": "Co mat",
  "image_base64": "data:image/jpeg;base64,...",
  "session_start": "2026-05-31 08:00:00",
  "lat": 10.0452,
  "lng": 105.7469
}
```

**Quy tắc bảo mật:**
- Sinh viên **chỉ được điểm danh cho chính mình** (MSSV tự động gán từ token)
- Admin được điểm danh cho bất kỳ sinh viên nào
- **Phải có phiên điểm danh đang mở** (`trang_thai = 1`) cho lớp đó
- **GPS Geofencing**: Nếu sinh viên gửi tọa độ GPS, hệ thống kiểm tra khoảng cách tới lớp (công thức Haversine)
- **Khung giờ**: Cho phép sớm 15 phút, trễ 30 phút so với giờ bắt đầu phiên
- Ảnh bằng chứng được lưu vào `database/evidence/<YYYYMMDD>/`

**Response (200):**
```json
{
  "success": true,
  "message": "Ghi nhận điểm danh thành công",
  "data": {
    "mssv": "SV001",
    "action": "inserted",
    "do_chinh_xac": 0.95,
    "trang_thai": "Co mat",
    "evidence_path": "database/evidence/20260531/SV001_103045_a1b2c3d4.jpg"
  }
}
```

### POST `/api/mobile/checkout`
Checkout từ Mobile App.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "mssv": "SV001",
  "lop_id": 1,
  "camera_id": 0,
  "image_base64": "..."
}
```

---

## 3. Mobile API — Truy vấn dữ liệu

### GET `/api/mobile/stats`
Thống kê điểm danh hôm nay.

**Headers:** `Authorization: Bearer <token>`

**Response cho Admin:**
```json
{
  "success": true,
  "data": {
    "total": 50,
    "present": 42,
    "absent": 8,
    "date": "2026-05-31"
  }
}
```

**Response cho Sinh viên:**
- `total`: Tổng số phiên điểm danh hôm nay cho lớp của sinh viên
- `present`: Số phiên sinh viên đã có mặt
- `absent`: Số phiên vắng

### GET `/api/mobile/history`
Lịch sử điểm danh.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
| Param | Type | Mô tả |
|---|---|---|
| `limit` | int | Số lượng tối đa (mặc định: 200) |
| `mssv` | string | Lọc theo MSSV (sinh viên tự động gán) |
| `lop_id` | int | Lọc theo lớp |
| `date` | string | Lọc theo ngày (YYYY-MM-DD) |
| `month` | int | Lọc theo tháng (1-12) |
| `year` | int | Lọc theo năm |

**Bảo mật:** Sinh viên CHỈ xem được lịch sử của chính mình.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "thoi_gian": "2026-05-31 08:15:30",
      "trang_thai": "Co mat",
      "do_chinh_xac": 0.95,
      "ghi_chu": null,
      "ho_ten": "Nguyễn Văn A",
      "mssv": "SV001",
      "avatar": "SV001/0.jpg",
      "ma_lop": "CNTT01",
      "evidence_path": "database/evidence/20260531/SV001_081530_abcd1234.jpg"
    }
  ]
}
```

### GET `/api/mobile/profile`
Thông tin cá nhân người dùng đang đăng nhập.

**Headers:** `Authorization: Bearer <token>`

**Response cho Sinh viên:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "mssv": "SV001",
    "ho_ten": "Nguyễn Văn A",
    "email": "sv001@mtu.edu.vn",
    "sdt": "0901234567",
    "lop_id": 1,
    "ten_lop": "Công nghệ thông tin K16",
    "ma_lop": "CNTT01",
    "avatar": "SV001/0.jpg",
    "da_train": 1,
    "ngay_sinh": "2004-03-15",
    "gioi_tinh": 1,
    "trang_thai": 1,
    "created_at": "2026-01-15 10:00:00"
  }
}
```

### GET `/api/mobile/classes`
Danh sách lớp học (không yêu cầu auth).

**Response:**
```json
{
  "success": true,
  "data": [
    {"id": 1, "ma_lop": "CNTT01", "ten_lop": "Công nghệ thông tin K16"},
    {"id": 2, "ma_lop": "KTPM01", "ten_lop": "Kỹ thuật phần mềm K16"}
  ]
}
```

---

## 4. Mobile API — Đăng ký khuôn mặt

### POST `/api/mobile/register_face`
Đăng ký khuôn mặt cho sinh viên (không yêu cầu token).

**Request Body:**
```json
{
  "mssv": "SV001",
  "ho_ten": "Nguyễn Văn A",
  "lop_id": 1,
  "images": [
    "data:image/jpeg;base64,...",
    "data:image/jpeg;base64,...",
    "data:image/jpeg;base64,..."
  ]
}
```

**Logic xử lý:**
- **Sinh viên mới**: Tự động tạo record trong `sinh_vien` với mật khẩu mặc định `123456`
- **Sinh viên đã tồn tại**: Kiểm tra họ tên khớp → cập nhật ảnh
- Ảnh lưu vào `database/<MSSV>/0.jpg, 1.jpg, ...`

**Response (200):**
```json
{
  "success": true,
  "message": "Đã đăng ký tài khoản và lưu thành công 3 ảnh khuôn mặt.",
  "data": {"mssv": "SV001", "images_saved": 3}
}
```

---

## 5. Mobile API — Tài khoản

### POST `/api/mobile/change-password`
Đổi mật khẩu.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "old_password": "mật_khẩu_cũ",
  "new_password": "mật_khẩu_mới"
}
```

### POST `/api/mobile/fcm-token`
Cập nhật Firebase Cloud Messaging token cho push notification.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "fcm_token": "firebase_cloud_messaging_device_token"
}
```

---

## 6. Mobile API — Quản lý điểm danh (Admin only)

### DELETE `/api/mobile/attendance/<record_id>`
Xóa 1 bản ghi điểm danh. Chỉ Admin mới có quyền.

### DELETE `/api/mobile/attendance/clear`
Xóa toàn bộ lịch sử điểm danh. Chỉ Admin mới có quyền.

---

## 7. Web Routes — Dashboard & Quản lý

| Route | Mô tả |
|---|---|
| `/` | Trang đăng nhập |
| `/dashboard` | Bảng điều khiển tổng quan |
| `/students` | Quản lý sinh viên (CRUD, import Excel, chụp ảnh) |
| `/classes` | Quản lý lớp học |
| `/attendance` | Điểm danh (mở phiên, Kiosk mode, nhận diện realtime) |
| `/training` | Huấn luyện AI (Train All, Train One, xem tiến độ) |
| `/export` | Xuất báo cáo Excel/PDF |
| `/cameras` | Quản lý camera |
| `/fraud` | Xem log gian lận |
| `/chatbot` | AI Chatbot |

---

## 8. Chatbot API

### GET `/chatbot/`
Trang giao diện chat AI.

### POST `/chatbot/ask`
Gửi câu hỏi cho AI.

**Request Body:**
```json
{"question": "Hệ thống điểm danh hoạt động như thế nào?"}
```

**Response:**
```json
{
  "answer": "Hệ thống điểm danh MTUFace hoạt động theo quy trình...",
  "sources": [
    {"file": "bao_cao_do_an.md", "category": "documentation"},
    {"file": "core/engine.py", "category": "core"}
  ],
  "duration_ms": 1500,
  "backend": "gemini"
}
```

### POST `/chatbot/build-knowledge`
Xây dựng/rebuild kho tri thức AI.

### GET `/chatbot/knowledge-progress`
SSE (Server-Sent Events) stream tiến độ build.

### GET `/chatbot/knowledge-status`
Trạng thái kho tri thức (số chunks, lần build cuối, danh sách nguồn).

### POST `/chatbot/clear`
Xóa lịch sử chat hiện tại.

---

## 9. Mã lỗi HTTP

| Code | Mô tả |
|---|---|
| `200` | Thành công |
| `400` | Thiếu dữ liệu hoặc dữ liệu không hợp lệ |
| `401` | Chưa đăng nhập / Token hết hạn |
| `403` | Không có quyền (Device Binding, GPS ngoài phạm vi, phiên chưa mở) |
| `404` | Không tìm thấy tài nguyên |
| `409` | Conflict (điểm danh bị cooldown / đã ghi trước đó) |
| `500` | Lỗi server |

---

## 10. Kiến trúc kỹ thuật API

### Flow xử lý request Mobile
```
Mobile App → HTTP Request → Flask Route (routes/api_mobile.py)
  → JWT Middleware (_require_mobile_auth)
  → Business Logic (services/)
  → Database (db/connection.py → MySQL)
  → JSON Response
```

### Realtime Communication
```
Web Kiosk ↔ SocketIO ↔ Flask Backend
  → Recognition Thread (services/recognition_thread.py)
  → AI Engine (core/engine.py → detect_and_embed)
  → Matcher (core/matcher.py → cosine similarity)
  → Attendance Service → Database
  → SocketIO emit → Update UI
```

### Push Notification Flow
```
Điểm danh thành công → FCM Service (services/fcm_service.py)
  → Firebase Admin SDK → Push to Student's Mobile App
  → Telegram Alert (services/telegram_alert.py) → Telegram Bot
```
