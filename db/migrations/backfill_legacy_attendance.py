import sys
import os

# Ensure we can import from db.connection
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from db.connection import execute_update, execute_one, execute_query


def backfill():
    print("Starting migration: Backfill legacy attendance records")
    try:
        # Check how many records have status = NULL or trang_thai = 'Co mat' without proper status
        sql_check = "SELECT COUNT(*) as cnt FROM diem_danh WHERE status = 'PRESENT' OR trang_thai = 'Co mat' OR status IS NULL"
        # We want to backfill records that have trang_thai = 'Co mat' but status might not be set right

        # Actually, let's just make sure all 'Co mat' are 'PRESENT'
        res1 = execute_update(
            "UPDATE diem_danh SET status = 'PRESENT' WHERE trang_thai = 'Co mat' AND (status IS NULL OR status = '')"
        )
        print(f"Updated {res1} legacy 'Co mat' records to status = 'PRESENT'.")

        # Some records might just have status = NULL entirely
        res2 = execute_update(
            "UPDATE diem_danh SET status = 'PRESENT', trang_thai = 'Co mat' WHERE status IS NULL"
        )
        if res2 > 0:
            print(f"Updated {res2} completely null status records to PRESENT/Co mat.")

        print("Legacy attendance backfill completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")


if __name__ == "__main__":
    backfill()
