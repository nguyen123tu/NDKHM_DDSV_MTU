# 🚀 Kế Hoạch Triển Khai MTUFace - Kiến Trúc Offline-First

Dựa trên chuẩn [Offline-First Architecture của Google](https://developer.android.com/topic/architecture/data-layer/offline-first), dưới đây là bản danh sách chi tiết các công việc cần làm, chia thành 4 giai đoạn cốt lõi. Bạn có thể dùng danh sách này làm Checklist (đánh dấu hoàn thành) trong quá trình code.

---

## 🛠️ Giai Đoạn 1: Chuẩn Bị Phía Backend (Python / Flask)

Tạo cơ sở hạ tầng API và cấu trúc dữ liệu để hỗ trợ đồng bộ xuống Mobile App.

- [ ] **1.1. Thay đổi Database (MySQL/SQLite)**
  - Thêm cột `face_vector` (kiểu dữ liệu `TEXT` hoặc `JSON`) vào bảng `sinh_vien`.
  - Thêm cột `updated_at` (kiểu `TIMESTAMP`) vào bảng `sinh_vien` để phục vụ Delta Sync (chỉ kéo dữ liệu mới).
  
- [ ] **1.2. Chuyển đổi dữ liệu não bộ cũ**
  - Viết 1 script Python nhỏ đọc file `embeddings.pkl` hiện tại.
  - Convert mảng numpy của từng `mssv` sang mảng cơ bản (List), ép kiểu JSON chuỗi và `UPDATE` vào cột `face_vector` trong bảng `sinh_vien`.
  
- [ ] **1.3. Nâng cấp luồng Train Khuôn Mặt**
  - Trong quá trình Train, sau khi tạo ra vector và lưu vào `.pkl`, cần thực hiện thêm lệnh SQL để lưu chuỗi vector này vào cột `face_vector` của Database.

- [ ] **1.4. Xây dựng PULL API (Đồng bộ xuống)**
  - Viết route `GET /api/sync/students` trong Flask.
  - Nhận tham số `last_sync_time`. Trả về JSON danh sách sinh viên có `updated_at >= last_sync_time`, kèm theo mảng số `face_vector`.

- [ ] **1.5. Xây dựng PUSH API (Đồng bộ lên)**
  - Viết route `POST /api/sync/attendance` trong Flask.
  - Viết logic kiểm tra trùng lặp (Idempotency) bằng cách dò xem `local_uuid` do App gửi lên đã tồn tại trong CSDL chưa. Tránh ghi đúp điểm danh.

---

## 📱 Giai Đoạn 2: Xây Dựng Tầng Dữ Liệu Cục Bộ (Flutter - Local Storage)

Biến SQLite trên điện thoại thành "Nguồn chân lý" (Source of Truth) cho ứng dụng.

- [ ] **2.1. Cài đặt thư viện Flutter**
  - Thêm `sqflite`, `path_provider` (quản lý file DB).
  - Thêm `shared_preferences` (để lưu timestamp đồng bộ cuối cùng).

- [ ] **2.2. Khởi tạo Local DB (`app_database.dart`)**
  - Tạo bảng cục bộ `local_students`: `(mssv TEXT PRIMARY KEY, name TEXT, face_vector TEXT, updated_at TEXT)`.
  - Tạo bảng cục bộ `local_attendance`: `(local_uuid TEXT PRIMARY KEY, mssv TEXT, check_time TEXT, confidence REAL, sync_status INTEGER DEFAULT 0)`.

- [ ] **2.3. Áp dụng Repository Pattern**
  - Viết file `student_repository.dart`: Chứa hàm lấy danh sách SV từ SQLite cục bộ. Không gọi API ở file này!
  - Viết file `attendance_repository.dart`: Chứa hàm `saveAttendance()`. Khi camera quét thành công, gọi hàm này để INSERT vào SQLite với `sync_status = 0`. App lập tức báo "Điểm danh thành công" mà không cần đợi API.

---

## 🔄 Giai Đoạn 3: Cơ Chế Đồng Bộ Hóa (Flutter - Synchronization)

Nối cầu giao tiếp giữa Local DB (Flutter) và Remote DB (Flask) thông qua Backgound Sync.

- [ ] **3.1. Viết Sync Manager (`sync_manager.dart`)**
  - Hàm `pullData()`: Lấy `last_sync_time` từ SharedPreferences -> Gọi `GET /api/sync/students` -> Chèn mới/Cập nhật đè vào bảng `local_students` -> Lưu lại `last_sync_time` mới.
  - Hàm `pushData()`: Truy vấn bảng `local_attendance` lấy các dòng `sync_status == 0` -> Đóng gói thành mảng JSON gửi qua `POST /api/sync/attendance` -> Đổi `sync_status = 1` hoặc xóa log nếu Server trả về 200 OK.

- [ ] **3.2. Bắt sự kiện thay đổi mạng**
  - Cài package `connectivity_plus`.
  - Viết listener: Hễ thiết bị chuyển từ Offline sang Online (Wifi/4G), tự động gọi hàm `pushData()` trong nền.

- [ ] **3.3. Background Task (Tuỳ chọn Nâng Cao)**
  - Cài package `workmanager` để Android/iOS tự động gọi `pullData()` mỗi 1 tiếng ngay cả khi tắt App (để sáng hôm sau sinh viên mang máy đi học thì DB đã có sẵn data mới nhất).

---

## 🧠 Giai Đoạn 4: Tích Hợp AI Chạy Offline trên Flutter

Biến ứng dụng thành Kiosk di động tự nhận diện mà không cần Internet.

- [ ] **4.1. Chuẩn bị AI Model**
  - Tìm hoặc convert model TensorFlow Lite (ví dụ: MobileFaceNet.tflite - chỉ khoảng 4MB). Thêm vào thư mục `assets` của Flutter.

- [ ] **4.2. Cài đặt các package xử lý Camera & ML**
  - `camera` (mở webcam).
  - `google_mlkit_face_detection` (của Google, dùng để quét nhanh vị trí khuôn mặt - cắt ảnh mặt ra).
  - `tflite_flutter` (để chạy model MobileFaceNet ở trên ảnh mặt đã cắt).

- [ ] **4.3. Xây dựng luồng Nhận diện Offline**
  - Camera bắt được khuôn mặt -> Cắt ảnh mặt vuông.
  - Nhét ảnh mặt vào TFLite -> Nhận về mảng 512 con số thực.
  - Truy vấn SQLite kéo toàn bộ chuỗi vector của sinh viên ra, parse thành List.
  - Viết hàm toán học Cosine Similarity (tương tự như code Python) để so khớp mảng số của camera và mảng số trong DB.
  - Khớp -> Gọi `attendance_repository.saveAttendance()` -> Xong!
