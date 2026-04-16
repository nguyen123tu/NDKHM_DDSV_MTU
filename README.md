# NDKHM_DDSV_MTU - Hệ Thống Điểm Danh Sinh Viên Bằng Nhận Diện Khuôn Mặt

Đây là dự án hệ thống điểm danh sinh viên bằng công nghệ nhận diện khuôn mặt, trang bị các công nghệ AI hiện đại như InsightFace, YOLO, Flask và MySQL.

## Yêu cầu hệ thống
- Python 3.8+
- Cơ sở dữ liệu MySQL (hoặc Docker nếu chạy qua container)
- Cài đặt các thư viện trong `requirements.txt`

## Hướng dẫn Cài đặt

**1. Clone dự án và cài đặt thư viện**
```bash
git clone https://github.com/nguyen123tu/NDKHM_DDSV_MTU.git
cd NDKHM_DDSV_MTU
pip install -r requirements.txt
```

**2. Cấu hình Môi trường**
- Copy file `.env.example` thành `.env`:
```bash
cp .env.example .env
```
- Mở file `.env` và cập nhật các thông số bảo mật, CSDL MySQL của bạn:
  - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
  - Bạn cũng có thể thiết lập cấu hình AI Engine mong muốn (`insightface` hoặc `yolo_resnet`).

**3. Khởi tạo Cơ sở dữ liệu**
- Import các bảng bằng file `db_schema.sql` vào MySQL bằng một công cụ quản lý CSDL (như phpMyAdmin, DBeaver) hoặc tạo tự động qua docker.

## Sử dụng

Có khá nhiều script khác nhau để huấn luyện và điểm danh, tuỳ thuộc vào nhu cầu:
- Khởi động hệ thống Web Admin (Quản lý Sinh viên/Lớp học/Dữ liệu):
```bash
python app.py
```
- Nếu có file `05_main_system.py`, chạy nó để khởi chạy điểm danh trực tiếp qua Camera:
```bash
python 05_main_system.py
```

## Chú ý (Cấu hình nâng cao)
- **Cảnh báo Telegram**: Hãy điền `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` vào `.env` nếu bạn muốn nhận cảnh báo qua tin nhắn.
- **Docker**: Dự án có hỗ trợ Docker Compose. Thay vì cài Python và MySQL ở ngoài, bạn có thể chạy:
```bash
docker-compose up -d --build
```
