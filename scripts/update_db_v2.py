
import sys
import os
sys.path.append(os.getcwd())

from db.connection import execute_update, execute_one

def update():
    print("Updating database structure to v2...")
    
    # 1. Create table lich_hoc
    sql_lich_hoc = """
    CREATE TABLE IF NOT EXISTS lich_hoc (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        lop_id          INT,
        mon_hoc         VARCHAR(100) NOT NULL,
        thu             INT COMMENT '2=Thứ 2, ..., 8=Chủ nhật',
        tiet_bat_dau    INT,
        so_tiet         INT,
        phong_hoc       VARCHAR(50),
        giang_vien      VARCHAR(100),
        created_at      DATETIME DEFAULT NOW(),
        FOREIGN KEY (lop_id) REFERENCES lop_hoc(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        execute_update(sql_lich_hoc)
        print("Successfully created 'lich_hoc' table (if not exists).")
    except Exception as e:
        print(f"Error creating 'lich_hoc' table: {e}")
        return

    # 2. Update sinh_vien table to ensure all necessary fields for profile exist
    # (Email and SĐT already exist in schema.sql but let's be safe)
    res = execute_one("SELECT * FROM sinh_vien LIMIT 1")
    if res:
        fields = res.keys()
        if 'email' not in fields:
            execute_update("ALTER TABLE sinh_vien ADD COLUMN email VARCHAR(100) AFTER ho_ten")
            print("Added 'email' column to 'sinh_vien'.")
        if 'sdt' not in fields:
            execute_update("ALTER TABLE sinh_vien ADD COLUMN sdt VARCHAR(15) AFTER email")
            print("Added 'sdt' column to 'sinh_vien'.")

    print("\nDatabase update v2 completed!")

if __name__ == "__main__":
    update()
