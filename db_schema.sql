-- Tạo cơ sở dữ liệu nếu chưa có
CREATE DATABASE IF NOT EXISTS doan_nhandien CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE doan_nhandien;

-- Tạo bảng Users (Chứa thông tin Sinh Viên/Nhân viên)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_sv VARCHAR(20) UNIQUE NOT NULL,
    ho_ten VARCHAR(100) NOT NULL,
    file_anh VARCHAR(255) NOT NULL, -- Tên file ảnh (vd: 2021A123.jpg)
    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tạo bảng Lịch sử ra vào (điểm danh, cảnh báo)
CREATE TABLE IF NOT EXISTS lich_su_ra_vao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ma_sv VARCHAR(20),     -- Nếu là người lạ thì lưu rỗng hoặc 'UNKNOWN'
    thoi_gian TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trang_thai VARCHAR(50), -- 'Hợp Lệ' hoặc 'Cảnh Báo'
    FOREIGN KEY(ma_sv) REFERENCES users(ma_sv) ON DELETE SET NULL
);

-- Thêm một bản ghi mặc định cho "Kẻ lạ" để tránh lỗi khóa ngoại nếu cần
INSERT IGNORE INTO users (ma_sv, ho_ten, file_anh) VALUES ('UNKNOWN', 'Kẻ lạ (Chưa định danh)', 'none');
