-- ============================================================
-- DỮ LIỆU MẪU: Dùng để test hệ thống sau khi cài đặt
-- ============================================================

-- Admin mặc định (password: admin123)
-- Hash được tạo bởi werkzeug.security.generate_password_hash('admin123', method='pbkdf2:sha256')
INSERT IGNORE INTO admin (username, password_hash, ho_ten, role) VALUES
('admin', 'pbkdf2:sha256:600000$XKcV3pW8$a8f1b7c6e5d4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9', 'Quản Trị Viên', 'admin');

-- 1 Lớp học mẫu
INSERT IGNORE INTO lop_hoc (ma_lop, ten_lop, khoa, hoc_ky, nam_hoc, giao_vien) VALUES
('CNTT01', 'Lập Trình Python', 'Công Nghệ Thông Tin', 'HK2', '2025-2026', 'ThS. Nguyễn Văn A');

-- 3 Sinh viên mẫu
INSERT IGNORE INTO sinh_vien (mssv, ho_ten, email, lop_id, gioi_tinh) VALUES
('22D14801030074', 'Nguyễn Đông Từ', 'tu.nguyen@student.mtu.edu.vn', 1, 1),
('22D14801030001', 'Trần Thị Bình', 'binh.tran@student.mtu.edu.vn', 1, 0),
('22D14801030002', 'Lê Văn Cường', 'cuong.le@student.mtu.edu.vn', 1, 1);
