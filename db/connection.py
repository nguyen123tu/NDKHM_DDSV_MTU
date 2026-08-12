"""
Quản lý kết nối MS SQL Server (Được cập nhật tự động bằng AI dùng PyODBC).
Sử dụng Windows Authentication để bỏ qua mọi rắc rối về tài khoản 'sa' và TCP/IP.
"""

import pyodbc
from config import Config
import os
import threading
import re

_pool = None
_pool_lock = threading.Lock()


def build_conn_str(include_db=True):
    """Tạo chuỗi kết nối sử dụng Windows Authentication (Trusted_Connection)"""
    # Dùng ODBC Driver 18 for SQL Server (hoặc driver khác nếu máy user dùng bản cũ)
    driver = "{ODBC Driver 18 for SQL Server}"
    server = Config.DB_HOST
    conn_str = f"Driver={driver};Server={server};Trusted_Connection=yes;TrustServerCertificate=yes"
    if include_db:
        conn_str += f";Database={Config.DB_NAME}"
    return conn_str


def _pyodbc_creator():
    return pyodbc.connect(build_conn_str(include_db=True), autocommit=False)
_pyodbc_creator.dbapi = pyodbc


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                try:
                    from dbutils.pooled_db import PooledDB
                    
                    max_conn = Config.DB_MAX_CONNECTIONS if hasattr(Config, "DB_MAX_CONNECTIONS") else 20
                    blocking = Config.DB_POOL_BLOCKING if hasattr(Config, "DB_POOL_BLOCKING") else True

                    _pool = PooledDB(
                        creator=_pyodbc_creator,
                        maxconnections=max_conn,
                        mincached=2,
                        maxcached=10,
                        blocking=blocking,
                        failures=(pyodbc.Error, pyodbc.OperationalError)
                    )
                    print("[DB POOL] Đã khởi tạo kết nối Pool (PyODBC + Windows Auth)")
                except ImportError:
                    print("[DB POOL WARNING] Chưa cài DBUtils, sử dụng kết nối trực tiếp pyodbc")
                    _pool = "NO_POOL"
                except Exception as e:
                    print(f"[DB POOL ERROR] Loi khoi tao Pool: {e}")
                    _pool = "NO_POOL"
    return _pool


def get_db():
    """Lấy kết nối tới MS SQL Server (qua Pool nếu khả dụng)."""
    try:
        pool = _get_pool()
        if pool and pool != "NO_POOL":
            conn = pool.connection()
            return conn
        else:
            return _pyodbc_creator()
    except Exception as e:
        print(f"[DB ERROR] Khong the lay connection: {e}")
        return None


def close_db(conn):
    """Đóng hoặc trả kết nối về Pool."""
    if conn:
        try:
            conn.close()
        except Exception as e:
            print(f"[DB WARNING] Loi dong connection: {e}")


def _to_dict(cursor):
    """Chuyển đổi kết quả của pyodbc thành dictionary giống pymssql"""
    if cursor.description is None:
        return []
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _to_dict_one(cursor):
    if cursor.description is None:
        return None
    row = cursor.fetchone()
    if not row:
        return None
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def execute_query(sql, params=None, dictionary=True):
    """Thực thi câu lệnh SELECT, trả về list kết quả."""
    conn = get_db()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        # Chuyển đổi parameter từ %s của pymssql sang ? của pyodbc
        sql = sql.replace('%s', '?')
        
        if params is not None and len(params) == 0:
            params = None
            
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
            
        if dictionary:
            return _to_dict(cursor)
        return cursor.fetchall()
    except Exception as e:
        print(f"[DB ERROR] Query that bai: {e}\n  SQL: {sql}")
        return []
    finally:
        if "cursor" in locals():
            cursor.close()
        close_db(conn)


def execute_one(sql, params=None, dictionary=True):
    """Thực thi câu lệnh SELECT, trả về 1 bản ghi duy nhất."""
    conn = get_db()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        sql = sql.replace('%s', '?')
        
        if params is not None and len(params) == 0:
            params = None
            
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
            
        if dictionary:
            return _to_dict_one(cursor)
        return cursor.fetchone()
    except Exception as e:
        print(f"[DB ERROR] Query that bai: {e}\n  SQL: {sql}")
        return None
    finally:
        if "cursor" in locals():
            cursor.close()
        close_db(conn)


def execute_update(sql, params=None):
    """Thực thi câu lệnh INSERT/UPDATE/DELETE."""
    conn = get_db()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        sql = sql.replace('%s', '?')
        
        if params is not None and len(params) == 0:
            params = None
            
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
            
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        print(f"[DB ERROR] Update that bai: {e}\n  SQL: {sql}")
        return -1
    finally:
        if "cursor" in locals():
            cursor.close()
        close_db(conn)


class transaction:
    """Context manager cho multi-statement transaction."""
    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.conn = get_db()
        if self.conn is None:
            raise RuntimeError("Không thể lấy kết nối DB cho transaction")
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            except Exception as e:
                print(f"[DB ERROR] Transaction cleanup: {e}")
            finally:
                close_db(self.conn)
        return False


def init_database():
    """Khởi tạo Database và bảng từ schema.sql."""
    try:
        # Bước 1: Kết nối không DB để tạo DB
        setup_conn = pyodbc.connect(build_conn_str(include_db=False), autocommit=True)
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
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            conn = pyodbc.connect(build_conn_str(include_db=True), autocommit=True)
            cursor = conn.cursor()
            with open(schema_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            statements = [
                s.strip()
                for s in re.split(r"(?i)^\s*GO\s*$", sql_content, flags=re.MULTILINE)
                if s.strip()
            ]
            for stmt in statements:
                if stmt:
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        print(f"[DB ERROR] Error executing statement: {e}\nStatement: {stmt[:100]}...")
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


if __name__ == "__main__":
    print("Testing DB connection...")
    init_database()
    results = execute_query("SELECT 1 as test")
    print(f"Ket qua test: {results}")
