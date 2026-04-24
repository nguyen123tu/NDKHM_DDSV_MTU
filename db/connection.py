"""
Quản lý kết nối MySQL với Connection Pooling.
Tất cả các module khác PHẢI dùng file này để truy cập DB,
KHÔNG import trực tiếp mysql.connector ở nơi khác.
"""

import mysql.connector
from mysql.connector import pooling, Error
from config import Config

# Connection Pool — tái sử dụng kết nối thay vì tạo mới mỗi lần query
_pool = None


def _get_pool():
    """Khởi tạo connection pool (lazy init, chỉ tạo 1 lần duy nhất)"""
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="face_attendance_pool",
                pool_size=5,
                pool_reset_session=True,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False
            )
            print(f"[DB] Connection pool initialized (pool_size=5)")
        except Error as e:
            print(f"[DB LỖI] Không thể tạo connection pool: {e}")
            raise
    return _pool


def get_db():
    """Lấy 1 connection từ pool. Caller phải tự close() sau khi dùng xong."""
    try:
        pool = _get_pool()
        conn = pool.get_connection()
        return conn
    except Error as e:
        print(f"[DB LỖI] Không thể lấy connection: {e}")
        return None


def close_db(conn):
    """Trả connection về pool (đóng an toàn)"""
    if conn and conn.is_connected():
        conn.close()


def execute_query(sql, params=None, dictionary=True):
    """
    Thực thi câu lệnh SELECT, trả về list kết quả.
    
    Args:
        sql: Câu lệnh SQL (có thể chứa %s placeholder)
        params: Tuple tham số (nếu có)
        dictionary: True → trả về list[dict], False → list[tuple]
    
    Returns:
        list: Danh sách bản ghi, hoặc [] nếu lỗi
    """
    conn = get_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=dictionary)
        cursor.execute(sql, params)
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"[DB LỖI] Query thất bại: {e}\n  SQL: {sql}")
        return []
    finally:
        if cursor:
            cursor.close()
        close_db(conn)


def execute_one(sql, params=None, dictionary=True):
    """
    Thực thi câu lệnh SELECT, trả về 1 bản ghi duy nhất.
    
    Returns:
        dict hoặc None
    """
    conn = get_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=dictionary)
        cursor.execute(sql, params)
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"[DB LỖI] Query thất bại: {e}\n  SQL: {sql}")
        return None
    finally:
        if cursor:
            cursor.close()
        close_db(conn)


def execute_update(sql, params=None):
    """
    Thực thi câu lệnh INSERT/UPDATE/DELETE.
    
    Returns:
        int: lastrowid nếu INSERT, hoặc rowcount nếu UPDATE/DELETE.
             -1 nếu lỗi.
    """
    conn = get_db()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        # Nếu là INSERT thì trả về ID mới, ngược lại trả về số dòng ảnh hưởng
        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
    except Error as e:
        conn.rollback()
        print(f"[DB LỖI] Update thất bại: {e}\n  SQL: {sql}")
        return -1
    finally:
        if cursor:
            cursor.close()
        close_db(conn)


def init_database():
    """
    Khởi tạo Database và bảng từ schema.sql.
    Chạy 1 lần khi setup hệ thống.
    """
    import os

    try:
        # Bước 1: Tạo Database nếu chưa có
        setup_conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cursor = setup_conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        setup_conn.commit()
        cursor.close()
        setup_conn.close()
        print(f"[DB] Database '{Config.DB_NAME}' đã sẵn sàng.")

        # Bước 2: Chạy schema.sql để tạo bảng
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            conn = mysql.connector.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )
            cursor = conn.cursor()
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Tách và chạy từng câu SQL
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            for stmt in statements:
                if stmt:
                    try:
                        cursor.execute(stmt)
                    except Error as e:
                        # Bỏ qua lỗi "table already exists"
                        if e.errno != 1050:
                            print(f"[DB CẢNH BÁO] {e}")
            conn.commit()
            cursor.close()
            conn.close()
            print("[DB] Schema đã được khởi tạo thành công.")
        else:
            print(f"[DB CẢNH BÁO] Không tìm thấy file schema.sql tại {schema_path}")

    except Error as e:
        print(f"[DB LỖI] Khởi tạo thất bại: {e}")
        raise


def seed_database():
    """Nạp dữ liệu mẫu từ seed.sql"""
    import os

    seed_path = os.path.join(os.path.dirname(__file__), 'seed.sql')
    if not os.path.exists(seed_path):
        print("[DB] Không tìm thấy seed.sql, bỏ qua.")
        return

    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        cursor = conn.cursor()
        with open(seed_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        for stmt in statements:
            if stmt:
                try:
                    cursor.execute(stmt)
                except Error as e:
                    # Bỏ qua lỗi duplicate entry
                    if e.errno != 1062:
                        print(f"[DB CẢNH BÁO SEED] {e}")
        conn.commit()
        cursor.close()
        conn.close()
        print("[DB] Dữ liệu mẫu đã được nạp thành công.")
    except Error as e:
        print(f"[DB LỖI] Seed thất bại: {e}")


if __name__ == '__main__':
    # Test kết nối
    print("Testing DB connection...")
    init_database()
    results = execute_query("SELECT 1 as test")
    print(f"Kết quả test: {results}")
