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
    password_hash VARCHAR(255) COMMENT 'Mật khẩu mặc định là MSSV',
    ho_ten      VARCHAR(100) NOT NULL,
    email       VARCHAR(100),
    sdt         VARCHAR(15),
    lop_id      INT,
    avatar      VARCHAR(255) COMMENT 'Tên file ảnh đại diện',
    da_train    TINYINT DEFAULT 0 COMMENT '0=chưa train, 1=đã train',
    ngay_sinh   DATE,
    gioi_tinh   TINYINT COMMENT '0=nữ, 1=nam',
    trang_thai  TINYINT DEFAULT 1 COMMENT '1=active, 0=inactive',
    trang_thai_face TINYINT DEFAULT 0 COMMENT '0=chưa đk, 1=chờ duyệt, 2=đã duyệt, 3=chụp lại',
    face_vector TEXT COMMENT 'JSON mảng 512 số phục vụ đồng bộ offline',
    device_id   VARCHAR(255) COMMENT 'Device ID để chống đăng nhập nhiều thiết bị',
    fcm_token   VARCHAR(255) COMMENT 'Token để nhận Push Notification',
    is_locked   TINYINT DEFAULT 0 COMMENT '0=bt, 1=khóa do gian lận',
    created_at  DATETIME DEFAULT NOW(),
    updated_at  DATETIME DEFAULT NOW() ON UPDATE CURRENT_TIMESTAMP,
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
    fcm_token       VARCHAR(255) COMMENT 'Token để nhận Push Notification',
    created_at      DATETIME DEFAULT NOW()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Bảng THÔNG BÁO (Thông báo cho sinh viên)
CREATE TABLE IF NOT EXISTS thong_bao (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    sinh_vien_id    INT,
    tieu_de         VARCHAR(255),
    noi_dung        TEXT,
    da_doc          TINYINT DEFAULT 0 COMMENT '0=chưa đọc, 1=đã đọc',
    created_at      DATETIME DEFAULT NOW(),
    FOREIGN KEY (sinh_vien_id) REFERENCES sinh_vien(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Bảng CẢNH BÁO GIAN LẬN (Gian lận điểm danh)
CREATE TABLE IF NOT EXISTS gian_lan_log (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    thoi_gian       DATETIME DEFAULT NOW(),
    sinh_vien_id    INT NULL,
    loai_gian_lan   VARCHAR(50) NOT NULL COMMENT 'Fake GPS, Spoofing, Khác',
    chi_tiet        TEXT,
    hinh_anh        VARCHAR(255) COMMENT 'Đường dẫn ảnh bằng chứng (nếu có)',
    da_xu_ly        TINYINT DEFAULT 0 COMMENT '0=chưa xử lý, 1=đã xử lý',
    FOREIGN KEY (sinh_vien_id) REFERENCES sinh_vien(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Bảng PHIÊN ĐIỂM DANH (Admin mở phiên, SV tham gia)
CREATE TABLE IF NOT EXISTS phien_diem_danh (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    lop_id      INT NOT NULL,
    admin_id    INT,
    trang_thai  TINYINT DEFAULT 1 COMMENT '1=đang mở, 0=đã đóng',
    mo_ta       VARCHAR(255),
    bat_dau     DATETIME DEFAULT NOW(),
    ket_thuc    DATETIME NULL,
    het_han     DATETIME NULL COMMENT 'Thời gian tự động đóng',
    vi_do       DOUBLE NULL COMMENT 'Latitude GPS của admin',
    kinh_do     DOUBLE NULL COMMENT 'Longitude GPS của admin',
    created_at  DATETIME DEFAULT NOW(),
    INDEX idx_lop_id (lop_id),
    INDEX idx_trang_thai (trang_thai),
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
