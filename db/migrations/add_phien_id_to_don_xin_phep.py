import sys
import os

# Ensure we can import from db.connection
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from db.connection import execute_update


def migrate():
    print("Starting migration: Add phien_id to don_xin_phep")
    try:
        # Check if column exists
        sql_check = """
        SELECT COUNT(*) as cnt 
        FROM sys.columns 
        WHERE Name = N'phien_id' AND Object_ID = Object_ID(N'don_xin_phep')
        """
        from db.connection import execute_one

        res = execute_one(sql_check)

        if res and res["cnt"] == 0:
            print("Adding phien_id column to don_xin_phep...")
            execute_update("ALTER TABLE don_xin_phep ADD phien_id INT NULL")
            execute_update("""
                ALTER TABLE don_xin_phep 
                ADD CONSTRAINT FK_don_xin_phep_phien 
                FOREIGN KEY (phien_id) REFERENCES phien_diem_danh(id) ON DELETE CASCADE
            """)
            print("Migration completed successfully.")
        else:
            print("Column phien_id already exists in don_xin_phep. Skipping.")
    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    migrate()
