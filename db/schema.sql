-- ============================================================
-- SCHEMA DATABASE: HỆ THỐNG ĐIỂM DANH NHẬN DIỆN KHUÔN MẶT
-- Charset: UTF8MB4 (hỗ trợ tiếng Việt đầy đủ)
-- Thứ tự tạo bảng: lop_hoc → sinh_vien → diem_danh (do FK)
-- ============================================================

-- 1. Bảng LỚP HỌC
CREATE TABLE IF NOT EXISTS lop_hoc (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    ma_lop      VARCHAR(20) NOT NULL UNIQUE,
    ten_lop     VARCHAR(100) NOT NULL,
    khoa        VARCHAR(100),
    hoc_ky      VARCHAR(20),
    nam_hoc     VARCHAR(10),
    giao_vien   VARCHAR(100),
    mo_ta       TEXT,
    trang_thai  TINYINT DEFAULT 1 COMMENT '1=active, 0=inactive',
    created_at  DATETIME DEFAULT NOW(),
    INDEX idx_ma_lop (ma_lop)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Bảng SINH VIÊN
CREATE TABLE IF NOT EXISTS sinh_vien (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    mssv        VARCHAR(20) NOT NULL UNIQUE,
    ho_ten      VARCHAR(100) NOT NULL,
    email       VARCHAR(100),
    sdt         VARCHAR(15),
    lop_id      INT,
    avatar      VARCHAR(255) COMMENT 'Tên file ảnh đại diện',
    da_train    TINYINT DEFAULT 0 COMMENT '0=chưa train, 1=đã train',
    ngay_sinh   DATE,
    gioi_tinh   TINYINT COMMENT '0=nữ, 1=nam',
    trang_thai  TINYINT DEFAULT 1 COMMENT '1=active, 0=inactive',
    created_at  DATETIME DEFAULT NOW(),
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE SET NULL,
    INDEX idx_mssv (mssv),
    INDEX idx_lop_id (lop_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Bảng ĐIỂM DANH
CREATE TABLE IF NOT EXISTS diem_danh (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    sinh_vien_id    INT,
    lop_id          INT,
    thoi_gian       DATETIME DEFAULT NOW() COMMENT 'Giờ vào (check-in)',
    gio_ra          DATETIME NULL COMMENT 'Giờ ra (check-out)',
    trang_thai      VARCHAR(20) DEFAULT 'Co mat' COMMENT 'Co mat / Tre / Canh bao',
    do_chinh_xac    FLOAT COMMENT 'Similarity score 0.0 - 1.0',
    camera_id       INT DEFAULT 0,
    ghi_chu         TEXT,
    INDEX idx_sv_id (sinh_vien_id),
    INDEX idx_lop_id (lop_id),
    INDEX idx_thoi_gian (thoi_gian),
    FOREIGN KEY (sinh_vien_id) REFERENCES sinh_vien(id) ON DELETE SET NULL,
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Bảng CAMERA
CREATE TABLE IF NOT EXISTS camera (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    ten_cam         VARCHAR(100) NOT NULL,
    loai            VARCHAR(20) DEFAULT 'USB' COMMENT 'USB / IP / RTSP / RTMP',
    url_hoac_index  VARCHAR(255) COMMENT '0 hoặc rtsp://...',
    vi_tri          VARCHAR(100),
    do_phan_giai    VARCHAR(20) DEFAULT 'Auto',
    trang_thai      TINYINT DEFAULT 1 COMMENT '1=active, 0=inactive',
    created_at      DATETIME DEFAULT NOW()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Bảng CẢNH BÁO (Phát hiện người lạ)
CREATE TABLE IF NOT EXISTS canh_bao (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    thoi_gian   DATETIME DEFAULT NOW(),
    camera_id   INT,
    anh_chup    VARCHAR(255) COMMENT 'Đường dẫn ảnh chụp kẻ lạ',
    da_xu_ly    TINYINT DEFAULT 0 COMMENT '0=chưa xử lý, 1=đã xử lý',
    ghi_chu     TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Bảng ADMIN (Người quản trị)
CREATE TABLE IF NOT EXISTS admin (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    ho_ten          VARCHAR(100),
    role            VARCHAR(20) DEFAULT 'admin' COMMENT 'admin / teacher',
    created_at      DATETIME DEFAULT NOW()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
