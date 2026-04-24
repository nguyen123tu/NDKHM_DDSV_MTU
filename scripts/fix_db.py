
import sys
import os
sys.path.append(os.getcwd())

from db.connection import execute_update, execute_query, execute_one
from werkzeug.security import generate_password_hash

def fix():
    print("Checking database structure...")
    
    # 1. Check if password_hash exists in sinh_vien
    res = execute_one("SELECT * FROM sinh_vien LIMIT 1")
    if res and 'password_hash' in res:
        print("Column 'password_hash' already exists in 'sinh_vien'.")
    else:
        print("Adding 'password_hash' column to 'sinh_vien' table...")
        try:
            execute_update("ALTER TABLE sinh_vien ADD COLUMN password_hash VARCHAR(255) AFTER mssv")
            print("Successfully added 'password_hash' column.")
        except Exception as e:
            print(f"Error adding column: {e}")
            return

    # 2. Update passwords for existing students
    print("Updating passwords for existing students (setting default password = MSSV)...")
    students = execute_query("SELECT id, mssv FROM sinh_vien")
    count = 0
    for s in students:
        pwd_hash = generate_password_hash(s['mssv'], method='pbkdf2:sha256')
        execute_update("UPDATE sinh_vien SET password_hash = %s WHERE id = %s", (pwd_hash, s['id']))
        count += 1
    
    print(f"Successfully updated passwords for {count} students.")
    print("\nDatabase fix completed!")

if __name__ == "__main__":
    fix()
