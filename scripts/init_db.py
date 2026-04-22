"""
Khởi tạo database và seed dữ liệu mẫu.

Chạy:
    python scripts/init_db.py
"""

from db.connection import init_database, seed_database


def main():
    init_database()
    seed_database()
    print("[OK] Database đã được khởi tạo.")


if __name__ == "__main__":
    main()
