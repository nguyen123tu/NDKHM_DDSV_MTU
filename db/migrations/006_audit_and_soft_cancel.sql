-- =========================================================================
-- MIGRATION 006: Audit log, soft-cancel phiên, require_gps, client_event_id
-- =========================================================================

-- 1. Bảng audit log chỉnh sửa điểm danh
IF OBJECT_ID('attendance_audit_log', 'U') IS NULL
BEGIN
    CREATE TABLE attendance_audit_log (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        attendance_id   INT NOT NULL,
        old_status      NVARCHAR(30),
        new_status      NVARCHAR(30) NOT NULL,
        changed_by      INT NULL,
        changed_at      DATETIME DEFAULT GETDATE(),
        reason          NVARCHAR(500) NOT NULL,
        FOREIGN KEY (attendance_id) REFERENCES diem_danh(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by) REFERENCES admin(id) ON DELETE SET NULL
    );

    CREATE INDEX idx_audit_attendance_id ON attendance_audit_log(attendance_id);
    CREATE INDEX idx_audit_changed_at ON attendance_audit_log(changed_at);
END;

-- 2. Soft-cancel cho phien_diem_danh
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'is_cancelled')
BEGIN
    ALTER TABLE phien_diem_danh ADD is_cancelled TINYINT DEFAULT 0;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'cancelled_by')
BEGIN
    ALTER TABLE phien_diem_danh ADD cancelled_by INT NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'cancelled_at')
BEGIN
    ALTER TABLE phien_diem_danh ADD cancelled_at DATETIME NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'cancel_reason')
BEGIN
    ALTER TABLE phien_diem_danh ADD cancel_reason NVARCHAR(255) NULL;
END;

-- 3. require_gps cho phien_diem_danh
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('phien_diem_danh') AND name = 'require_gps')
BEGIN
    ALTER TABLE phien_diem_danh ADD require_gps TINYINT DEFAULT 0;
END;

-- 4. client_event_id cho diem_danh (offline sync dedup)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('diem_danh') AND name = 'client_event_id')
BEGIN
    ALTER TABLE diem_danh ADD client_event_id NVARCHAR(100) NULL;
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_diem_danh_client_event_id' AND object_id = OBJECT_ID('diem_danh'))
BEGIN
    CREATE INDEX idx_diem_danh_client_event_id ON diem_danh(client_event_id);
END;
