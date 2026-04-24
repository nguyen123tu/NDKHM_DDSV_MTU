
from db.connection import execute_update

def extend_student_db():
    print("Starting student DB extension...")
    
    # List of columns to add
    columns = [
        ("dan_toc", "VARCHAR(50) DEFAULT 'Kinh'"),
        ("nien_khoa", "VARCHAR(20)"),
        ("tinh_trang", "INT DEFAULT 1"), # 1: Active, 0: Inactive
        ("cmnd_cccd", "VARCHAR(20)"),
        ("que_quan", "VARCHAR(255)"),
        ("ngay_sinh", "DATE")
    ]
    
    for col_name, col_type in columns:
        try:
            execute_update(f"ALTER TABLE sinh_vien ADD COLUMN {col_name} {col_type}")
            print(f" - Added column {col_name}")
        except Exception as e:
            if "Duplicate column" in str(e) or "already exists" in str(e).lower():
                print(f" - Column {col_name} already exists, skipping.")
            else:
                print(f" - Error adding column {col_name}: {e}")

    print("DB extension complete!")

if __name__ == "__main__":
    extend_student_db()
