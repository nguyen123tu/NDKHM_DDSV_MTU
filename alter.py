import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.connection import execute_update

def alter_table():
    try:
        execute_update("ALTER TABLE diem_danh ADD COLUMN gio_vao_lop TIME DEFAULT '07:00:00'")
        print("Column added successfully or already exists.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    alter_table()
