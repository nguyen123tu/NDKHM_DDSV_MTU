"""
Quản lý kết nối MS SQL Server.
Tất cả các module khác PHẢI dùng file này để truy cập DB.
"""

import pymssql
from config import Config
import os

def get_db():
    """Lấy kết nối tới MS SQL Server."""
    try:
        conn = pymssql.connect(
            server=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            as_dict=True,
            autocommit=False
        )
        return conn
    except Exception as e:
        print(f"[DB ERROR] Khong the lay connection: {e}")
        return None

def close_db(conn):
    """Đóng kết nối."""
    if conn:
        conn.close()

def execute_query(sql, params=None, dictionary=True):
    """
    Thực thi câu lệnh SELECT, trả về list kết quả.
    """
    conn = get_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(as_dict=dictionary)
        if params is not None and len(params) == 0:
            params = None
        cursor.execute(sql, params)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"[DB ERROR] Query that bai: {e}\n  SQL: {sql}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        close_db(conn)

def execute_one(sql, params=None, dictionary=True):
    """
    Thực thi câu lệnh SELECT, trả về 1 bản ghi duy nhất.
    """
    conn = get_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(as_dict=dictionary)
        if params is not None and len(params) == 0:
            params = None
        cursor.execute(sql, params)
        result = cursor.fetchone()
        return result
    except Exception as e:
        print(f"[DB ERROR] Query that bai: {e}\n  SQL: {sql}")
        return None
    finally:
        if 'cursor' in locals():
            cursor.close()
        close_db(conn)

def execute_update(sql, params=None):
    """
    Thực thi câu lệnh INSERT/UPDATE/DELETE.
    """
    conn = get_db()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        if params is not None and len(params) == 0:
            params = None
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] Update that bai: {e}\n  SQL: {sql}")
        return -1
    finally:
        if 'cursor' in locals():
            cursor.close()
        close_db(conn)

def init_database():
    """Khởi tạo Database và bảng từ schema.sql."""
    try:
        # Bước 1: Kết nối không DB để tạo DB
        setup_conn = pymssql.connect(
            server=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            autocommit=True
        )
        cursor = setup_conn.cursor()
        
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = N'{Config.DB_NAME}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE [{Config.DB_NAME}]")
            print(f"[DB] Database '{Config.DB_NAME}' da duoc tao.")
        else:
            print(f"[DB] Database '{Config.DB_NAME}' da san sang.")
            
        cursor.close()
        setup_conn.close()

        # Bước 2: Chạy schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            conn = pymssql.connect(
                server=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                autocommit=True
            )
            cursor = conn.cursor()
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            for stmt in statements:
                if stmt:
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        print(f"[DB WARNING] {e}")
            cursor.close()
            conn.close()
            print("[DB] Schema da duoc khoi tao thanh cong.")
        else:
            print(f"[DB WARNING] Khong tim thay file schema.sql tai {schema_path}")

    except Exception as e:
        print(f"[DB ERROR] Khoi tao that bai: {e}")
        raise

def seed_database():
    print("[DB] Seed cho MSSQL chua duoc cau hinh. Bo qua.")

if __name__ == '__main__':
    print("Testing DB connection...")
    init_database()
    results = execute_query("SELECT 1 as test")
    print(f"Ket qua test: {results}")
