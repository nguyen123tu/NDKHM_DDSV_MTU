import mysql.connector
from mysql.connector import Error

# --- CẤU HÌNH KẾT NỐI DATABASE ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "" # Mặc định XAMPP không có mật khẩu
DB_NAME = "doan_nhandien"

def create_connection():
    """Tạo kết nối tới cơ sở dữ liệu MySQL"""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"[DB LỖI] Không thể kết nối tới MySQL: {e}")
        return None

def log_attendance(ma_sv, status):
    conn = create_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO lich_su_ra_vao (ma_sv, trang_thai) VALUES (%s, %s)"
        cursor.execute(query, (ma_sv, status))
        conn.commit()
        return True
    except Error as e:
        print(f"[DB LỖI] Lỗi khi thêm log: {e}")
        return False
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def get_student_info(ma_sv):
    if ma_sv == "UNKNOWN" or ma_sv == "Kẻ Lạ (Unknown)":
        return "Kẻ Lạ"
    conn = create_connection()
    if conn is None: return ma_sv
    try:
        cursor = conn.cursor()
        query = "SELECT ho_ten FROM users WHERE ma_sv = %s"
        cursor.execute(query, (ma_sv,))
        record = cursor.fetchone()
        if record: return record[0]
        else: return ma_sv
    except Error as e:
        return ma_sv
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

# CÁC HÀM API DÀNH RIÊNG CHO WEB ADMIN PORTAL =================

def get_all_students():
    """Lấy danh sách tất cả học sinh"""
    conn = create_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE ma_sv != 'UNKNOWN' ORDER BY id DESC")
        return cursor.fetchall()
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def add_student(ma_sv, ho_ten, file_anh):
    """Thêm một sinh viên mới vào CSDL"""
    conn = create_connection()
    if conn is None: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO users (ma_sv, ho_ten, file_anh) VALUES (%s, %s, %s)"
        cursor.execute(query, (ma_sv, ho_ten, file_anh))
        conn.commit()
        return True
    except Error as e:
        print(f"[DB LỖI] Lỗi thêm SV: {e}")
        return False
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def get_all_logs(limit=50):
    """Lấy danh sách lịch sử ra vào mới nhất"""
    conn = create_connection()
    if conn is None: return []
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT l.id, l.ma_sv, l.thoi_gian, l.trang_thai, u.ho_ten, u.file_anh 
            FROM lich_su_ra_vao l
            LEFT JOIN users u ON l.ma_sv = u.ma_sv
            ORDER BY l.id DESC LIMIT %s
        """
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

def get_dashboard_stats():
    """Lấy thống kê căn bản cho giao diện"""
    conn = create_connection()
    if conn is None: return {"total_students": 0, "logs_today": 0, "warnings_today": 0}
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {}
        # Đếm Sinh Viên
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE ma_sv != 'UNKNOWN'")
        stats["total_students"] = cursor.fetchone()["count"]
        # Đếm Log Hôm Nay
        cursor.execute("SELECT COUNT(*) as count FROM lich_su_ra_vao WHERE DATE(thoi_gian) = CURDATE() AND trang_thai='Hợp Lệ'")
        stats["logs_today"] = cursor.fetchone()["count"]
        # Đếm Cảnh Báo Hôm Nay
        cursor.execute("SELECT COUNT(*) as count FROM lich_su_ra_vao WHERE DATE(thoi_gian) = CURDATE() AND trang_thai='Cảnh Báo'")
        stats["warnings_today"] = cursor.fetchone()["count"]
        return stats
    finally:
        if conn.is_connected(): cursor.close(); conn.close()

# Đoạn code tạo bảng tự động nếu dùng lần đầu
def init_database_if_not_exists():
    try:
        setup_conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
        cursor = setup_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        setup_conn.commit()
        cursor.close()
        setup_conn.close()
        
        conn = create_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ma_sv VARCHAR(20) UNIQUE NOT NULL,
                    ho_ten VARCHAR(100) NOT NULL,
                    file_anh VARCHAR(255) NOT NULL,
                    ngay_tao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lich_su_ra_vao (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    ma_sv VARCHAR(20),
                    thoi_gian TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trang_thai VARCHAR(50),
                    FOREIGN KEY(ma_sv) REFERENCES users(ma_sv) ON DELETE SET NULL
                )
            """)
            cursor.execute("INSERT IGNORE INTO users (ma_sv, ho_ten, file_anh) VALUES ('UNKNOWN', 'Kẻ lạ (Chưa định danh)', 'none');")
            conn.commit()
            print("[INFO] Đã khởi tạo hoàn tất cấu trúc CSDL.")
    except Exception as e:
        print(f"[CẢNH BÁO DB] Lỗi khởi tạo DB: {e}")

if __name__ == "__main__":
    init_database_if_not_exists()
