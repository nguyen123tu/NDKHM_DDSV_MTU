import pymysql

conn = pymysql.connect(host='localhost', user='root', password='', database='face_attendance')
c = conn.cursor()

# Fix bảng classes
classes_fix = [
    "ALTER TABLE classes ADD COLUMN subject VARCHAR(100) DEFAULT NULL",
    "ALTER TABLE classes ADD COLUMN teacher_name VARCHAR(100) DEFAULT NULL",
    "ALTER TABLE classes ADD COLUMN semester VARCHAR(20) DEFAULT NULL",
    "ALTER TABLE classes ADD COLUMN school_year VARCHAR(20) DEFAULT NULL",
    "ALTER TABLE classes ADD COLUMN status VARCHAR(10) DEFAULT 'active'",
    "ALTER TABLE classes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
]

# Fix bảng attendance_sessions
sessions_fix = [
    "ALTER TABLE attendance_sessions ADD COLUMN session_time TIME DEFAULT NULL",
    "ALTER TABLE attendance_sessions ADD COLUMN subject VARCHAR(100) DEFAULT NULL",
    "ALTER TABLE attendance_sessions ADD COLUMN note TEXT DEFAULT NULL",
    "ALTER TABLE attendance_sessions ADD COLUMN created_by INT DEFAULT NULL",
    "ALTER TABLE attendance_sessions ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    "ALTER TABLE attendance_sessions ADD COLUMN status VARCHAR(10) DEFAULT 'open'",
]

# Fix bảng attendance_records
records_fix = [
    "ALTER TABLE attendance_records ADD COLUMN check_in_time DATETIME DEFAULT NULL",
    "ALTER TABLE attendance_records ADD COLUMN confidence_score FLOAT DEFAULT NULL",
    "ALTER TABLE attendance_records ADD COLUMN method VARCHAR(10) DEFAULT 'face'",
    "ALTER TABLE attendance_records ADD COLUMN status VARCHAR(10) DEFAULT 'present'",
    "ALTER TABLE attendance_records ADD COLUMN note TEXT DEFAULT NULL",
    "ALTER TABLE attendance_records ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
]

for sql in classes_fix + sessions_fix + records_fix:
    try:
        c.execute(sql)
        col = sql.split("ADD COLUMN ")[1].split(" ")[0]
        tbl = sql.split("TABLE ")[1].split(" ")[0]
        print(f"OK: {tbl}.{col}")
    except Exception as e:
        print(f"Skip: {e}")

conn.commit()
conn.close()
print("\nDone! Tat ca bang da duoc cap nhat.")
