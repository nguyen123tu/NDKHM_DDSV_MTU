-- SCHEMA DATABASE: HỆ THỐNG ĐIỂM DANH NHẬN DIỆN KHUÔN MẶT
-- T-SQL for Microsoft SQL Server

IF OBJECT_ID('lop_hoc', 'U') IS NULL
CREATE TABLE lop_hoc (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    ma_lop      NVARCHAR(20) NOT NULL UNIQUE,
    ten_lop     NVARCHAR(100) NOT NULL,
    khoa        NVARCHAR(100),
    hoc_ky      NVARCHAR(20),
    nam_hoc     NVARCHAR(10),
    giao_vien   NVARCHAR(100),
    mo_ta       NVARCHAR(MAX),
    trang_thai  TINYINT DEFAULT 1,
    created_at  DATETIME DEFAULT GETDATE()
);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ma_lop' AND object_id = OBJECT_ID('lop_hoc'))
CREATE INDEX idx_ma_lop ON lop_hoc(ma_lop);

IF OBJECT_ID('sinh_vien', 'U') IS NULL
CREATE TABLE sinh_vien (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    mssv        NVARCHAR(20) NOT NULL UNIQUE,
    password_hash NVARCHAR(255),
    ho_ten      NVARCHAR(100) NOT NULL,
    email       NVARCHAR(100),
    sdt         NVARCHAR(15),
    lop_id      INT,
    avatar      NVARCHAR(255),
    da_train    TINYINT DEFAULT 0,
    ngay_sinh   DATE,
    gioi_tinh   TINYINT,
    trang_thai  TINYINT DEFAULT 1,
    trang_thai_face TINYINT DEFAULT 0,
    face_vector NVARCHAR(MAX),
    device_id   NVARCHAR(255),
    fcm_token   NVARCHAR(255),
    is_locked   TINYINT DEFAULT 0,
    created_at  DATETIME DEFAULT GETDATE(),
    updated_at  DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE SET NULL
);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_mssv' AND object_id = OBJECT_ID('sinh_vien'))
CREATE INDEX idx_mssv ON sinh_vien(mssv);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_lop_id' AND object_id = OBJECT_ID('sinh_vien'))
CREATE INDEX idx_lop_id ON sinh_vien(lop_id);

IF OBJECT_ID('diem_danh', 'U') IS NULL
CREATE TABLE diem_danh (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    sinh_vien_id    INT,
    lop_id          INT,
    thoi_gian       DATETIME DEFAULT GETDATE(),
    gio_vao_lop     TIME DEFAULT '07:00:00',
    trang_thai      NVARCHAR(20) DEFAULT 'Co mat',
    do_chinh_xac    FLOAT,
    camera_id       INT DEFAULT 0,
    ghi_chu         NVARCHAR(MAX),
    FOREIGN KEY (sinh_vien_id) REFERENCES sinh_vien(id) ON DELETE SET NULL,
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE SET NULL
);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_sv_id' AND object_id = OBJECT_ID('diem_danh'))
CREATE INDEX idx_sv_id ON diem_danh(sinh_vien_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_diem_danh_lop_id' AND object_id = OBJECT_ID('diem_danh'))
CREATE INDEX idx_diem_danh_lop_id ON diem_danh(lop_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_thoi_gian' AND object_id = OBJECT_ID('diem_danh'))
CREATE INDEX idx_thoi_gian ON diem_danh(thoi_gian);

IF OBJECT_ID('camera', 'U') IS NULL
CREATE TABLE camera (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    ten_cam         NVARCHAR(100) NOT NULL,
    loai            NVARCHAR(20) DEFAULT 'USB',
    url_hoac_index  NVARCHAR(255),
    vi_tri          NVARCHAR(100),
    do_phan_giai    NVARCHAR(20) DEFAULT 'Auto',
    trang_thai      TINYINT DEFAULT 1,
    created_at      DATETIME DEFAULT GETDATE()
);

IF OBJECT_ID('canh_bao', 'U') IS NULL
CREATE TABLE canh_bao (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    thoi_gian   DATETIME DEFAULT GETDATE(),
    camera_id   INT,
    anh_chup    NVARCHAR(255),
    da_xu_ly    TINYINT DEFAULT 0,
    ghi_chu     NVARCHAR(MAX)
);

IF OBJECT_ID('admin', 'U') IS NULL
CREATE TABLE admin (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    username        NVARCHAR(50) NOT NULL UNIQUE,
    password_hash   NVARCHAR(255) NOT NULL,
    ho_ten          NVARCHAR(100),
    role            NVARCHAR(20) DEFAULT 'admin',
    fcm_token       NVARCHAR(255),
    created_at      DATETIME DEFAULT GETDATE()
);

IF OBJECT_ID('thong_bao', 'U') IS NULL
CREATE TABLE thong_bao (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    sinh_vien_id    INT,
    tieu_de         NVARCHAR(255),
    noi_dung        NVARCHAR(MAX),
    da_doc          TINYINT DEFAULT 0,
    created_at      DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (sinh_vien_id) REFERENCES sinh_vien(id) ON DELETE CASCADE
);

IF OBJECT_ID('gian_lan_log', 'U') IS NULL
CREATE TABLE gian_lan_log (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    thoi_gian       DATETIME DEFAULT GETDATE(),
    sinh_vien_id    INT NULL,
    loai_gian_lan   NVARCHAR(50) NOT NULL,
    chi_tiet        NVARCHAR(MAX),
    hinh_anh        NVARCHAR(255),
    da_xu_ly        TINYINT DEFAULT 0,
    FOREIGN KEY (sinh_vien_id) REFERENCES sinh_vien(id) ON DELETE SET NULL
);

IF OBJECT_ID('phien_diem_danh', 'U') IS NULL
CREATE TABLE phien_diem_danh (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    lop_id      INT NOT NULL,
    admin_id    INT,
    trang_thai  TINYINT DEFAULT 1,
    mo_ta       NVARCHAR(255),
    bat_dau     DATETIME DEFAULT GETDATE(),
    ket_thuc    DATETIME NULL,
    het_han     DATETIME NULL,
    vi_do       FLOAT NULL,
    kinh_do     FLOAT NULL,
    created_at  DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE CASCADE
);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_phien_lop_id' AND object_id = OBJECT_ID('phien_diem_danh'))
CREATE INDEX idx_phien_lop_id ON phien_diem_danh(lop_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_trang_thai' AND object_id = OBJECT_ID('phien_diem_danh'))
CREATE INDEX idx_trang_thai ON phien_diem_danh(trang_thai);

IF OBJECT_ID('don_xin_phep', 'U') IS NULL
CREATE TABLE don_xin_phep (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    sinh_vien_id    INT NOT NULL,
    lop_id          INT NOT NULL,
    ly_do           NVARCHAR(MAX) NOT NULL,
    minh_chung_url  NVARCHAR(255),
    trang_thai      TINYINT DEFAULT 0,
    thoi_gian_tao   DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (sinh_vien_id) REFERENCES sinh_vien(id) ON DELETE CASCADE,
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE NO ACTION
);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_don_sv_id' AND object_id = OBJECT_ID('don_xin_phep'))
CREATE INDEX idx_don_sv_id ON don_xin_phep(sinh_vien_id);

IF OBJECT_ID('lich_hoc', 'U') IS NULL
CREATE TABLE lich_hoc (
    id          INT IDENTITY(1,1) PRIMARY KEY,
    lop_id      INT NOT NULL,
    thu         TINYINT NOT NULL,
    gio_bat_dau TIME NOT NULL,
    gio_ket_thuc TIME NULL,
    phong_hoc   NVARCHAR(50) NULL,
    ghi_chu     NVARCHAR(255) NULL,
    FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE CASCADE
);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_lich_lop_id' AND object_id = OBJECT_ID('lich_hoc'))
CREATE INDEX idx_lich_lop_id ON lich_hoc(lop_id);

