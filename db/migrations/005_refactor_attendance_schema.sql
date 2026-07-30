-- =========================================================================
-- MIGRATION 005: Tái cấu trúc cơ chế phiên điểm danh & sự kiện attendance
-- =========================================================================

-- 1. Bổ sung cột cho phien_diem_danh
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'loai_phien')
BEGIN
    ALTER TABLE phien_diem_danh ADD loai_phien NVARCHAR(20) DEFAULT 'MOBILE';
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'gio_hoc_du_kien')
BEGIN
    ALTER TABLE phien_diem_danh ADD gio_hoc_du_kien DATETIME NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'mo_checkin')
BEGIN
    ALTER TABLE phien_diem_danh ADD mo_checkin DATETIME NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'dong_checkin')
BEGIN
    ALTER TABLE phien_diem_danh ADD dong_checkin DATETIME NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'radius')
BEGIN
    ALTER TABLE phien_diem_danh ADD radius FLOAT DEFAULT 100;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'si_so_chot')
BEGIN
    ALTER TABLE phien_diem_danh ADD si_so_chot INT NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'nguoi_chot_id')
BEGIN
    ALTER TABLE phien_diem_danh ADD nguoi_chot_id INT NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'thoi_gian_chot')
BEGIN
    ALTER TABLE phien_diem_danh ADD thoi_gian_chot DATETIME NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'ban_sao_bao_cao')
BEGIN
    ALTER TABLE phien_diem_danh ADD ban_sao_bao_cao NVARCHAR(MAX) NULL;
END;

-- 2. Bổ sung cột cho diem_danh
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('diem_danh') AND name = 'phien_id')
BEGIN
    ALTER TABLE diem_danh ADD phien_id INT NULL;
    ALTER TABLE diem_danh ADD CONSTRAINT fk_diem_danh_phien FOREIGN KEY (phien_id) REFERENCES phien_diem_danh(id) ON DELETE CASCADE;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('diem_danh') AND name = 'status')
BEGIN
    ALTER TABLE diem_danh ADD status NVARCHAR(30) DEFAULT 'PRESENT';
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('diem_danh') AND name = 'late_minutes')
BEGIN
    ALTER TABLE diem_danh ADD late_minutes INT DEFAULT 0;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('diem_danh') AND name = 'method')
BEGIN
    ALTER TABLE diem_danh ADD method NVARCHAR(30) DEFAULT 'MOBILE_GPS';
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('diem_danh') AND name = 'verified_by')
BEGIN
    ALTER TABLE diem_danh ADD verified_by INT NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('diem_danh') AND name = 'updated_reason')
BEGIN
    ALTER TABLE diem_danh ADD updated_reason NVARCHAR(255) NULL;
END;

-- Tạo index cho phien_id trong diem_danh
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_diem_danh_phien_id' AND object_id = OBJECT_ID('diem_danh'))
BEGIN
    CREATE INDEX idx_diem_danh_phien_id ON diem_danh(phien_id);
END;

-- Tạo bảng attendance_events
IF OBJECT_ID('attendance_events', 'U') IS NULL
BEGIN
    CREATE TABLE attendance_events (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        phien_id        INT NOT NULL,
        sinh_vien_id    INT NOT NULL,
        event_type      NVARCHAR(30) DEFAULT 'FACE_OBSERVED',
        observed_at     DATETIME DEFAULT GETDATE(),
        camera_id       INT DEFAULT 0,
        confidence      FLOAT,
        evidence_path   NVARCHAR(255),
        FOREIGN KEY (phien_id) REFERENCES phien_diem_danh(id) ON DELETE CASCADE,
        FOREIGN KEY (sinh_vien_id) REFERENCES sinh_vien(id) ON DELETE CASCADE
    );

    CREATE INDEX idx_event_phien_id ON attendance_events(phien_id);
    CREATE INDEX idx_event_sv_id ON attendance_events(sinh_vien_id);
END;
