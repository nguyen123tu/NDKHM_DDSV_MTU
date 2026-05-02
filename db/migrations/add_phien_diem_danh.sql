-- ============================================================
-- MIGRATION: Thêm bảng PHIÊN ĐIỂM DANH (Attendance Session)
-- Bảng này lưu các phiên điểm danh do Admin tạo,
-- giúp sinh viên trên mobile biết lớp nào đang mở điểm danh.
-- ============================================================

CREATE TABLE IF NOT EXISTS phien_diem_danh (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    lop_id      INT NOT NULL,
    admin_id    INT COMMENT 'ID Admin tạo phiên',
    trang_thai  TINYINT DEFAULT 1 COMMENT '1=đang mở, 0=đã đóng',
    mo_ta       VARCHAR(255) COMMENT 'Ghi chú phiên điểm danh',
    bat_dau     DATETIME DEFAULT NOW() COMMENT 'Thời gian bắt đầu',
    ket_thuc    DATETIME NULL COMMENT 'Thời gian kết thúc (NULL nếu đang mở)',
    het_han     DATETIME NULL COMMENT 'Thời gian tự động hết hạn',
    vi_do       DOUBLE NULL COMMENT 'Vĩ độ GPS',
    kinh_do     DOUBLE NULL COMMENT 'Kinh độ GPS',
    created_at  DATETIME DEFAULT NOW(),
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE CASCADE,
    INDEX idx_lop_id (lop_id),
    INDEX idx_trang_thai (trang_thai),
    INDEX idx_bat_dau (bat_dau)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
