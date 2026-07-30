"""
Script chạy migration 006: audit log, soft-cancel, require_gps, client_event_id.
"""
import os
import sys
import pymssql

# Thêm project root vào path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
from config import Config

def run_migration():
    try:
        conn = pymssql.connect(
            server=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            autocommit=True
        )
        cursor = conn.cursor()

        migration_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '006_audit_and_soft_cancel.sql')
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # SQL Server batch separator
        batches = sql_content.split('\nGO\n')
        if len(batches) == 1:
            # Fallback: split by double newline after semicolons  
            # For IF...BEGIN...END blocks, execute entire script  
            try:
                cursor.execute(sql_content)
                print("[MIGRATION 006] Đã chạy toàn bộ migration thành công.")
            except Exception as e:
                # Try splitting by IF blocks
                statements = []
                current = []
                for line in sql_content.split('\n'):
                    if line.strip().startswith('IF ') and current:
                        statements.append('\n'.join(current))
                        current = [line]
                    else:
                        current.append(line)
                if current:
                    statements.append('\n'.join(current))

                for i, stmt in enumerate(statements):
                    stmt = stmt.strip()
                    if stmt and not stmt.startswith('--'):
                        try:
                            cursor.execute(stmt)
                            print(f"  [OK] Block {i+1}")
                        except Exception as ex:
                            print(f"  [SKIP] Block {i+1}: {ex}")
        else:
            for i, batch in enumerate(batches):
                batch = batch.strip()
                if batch:
                    try:
                        cursor.execute(batch)
                        print(f"  [OK] Batch {i+1}")
                    except Exception as ex:
                        print(f"  [SKIP] Batch {i+1}: {ex}")

        cursor.close()
        conn.close()
        print("[MIGRATION 006] Hoàn tất!")

    except Exception as e:
        print(f"[MIGRATION 006 ERROR] {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
