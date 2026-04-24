
from db.connection import execute_update

def mock_pending_face():
    mssv = '22D14801030074'
    # Set status to 1 (Pending)
    execute_update("UPDATE sinh_vien SET trang_thai_face = 1 WHERE mssv = %s", (mssv,))
    print(f"Done! Student {mssv} is now in 'Pending' status for face registration.")

if __name__ == "__main__":
    mock_pending_face()
