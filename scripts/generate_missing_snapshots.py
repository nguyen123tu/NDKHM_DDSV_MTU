import sys
import os
import json
from datetime import datetime

# Ensure we can import from services and db
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from db.connection import execute_query, execute_update, execute_one
from services.attendance_policy import get_session_attendance_summary

def generate():
    print("Starting snapshot generation for closed sessions without snapshot...")
    try:
        # Lấy danh sách phiên đã đóng nhưng chưa có ban_sao_bao_cao
        sessions = execute_query("SELECT id, lop_id, nguoi_chot_id FROM phien_diem_danh WHERE trang_thai = 0 AND ban_sao_bao_cao IS NULL")
        if not sessions:
            print("No sessions need snapshot generation.")
            return

        for session in sessions:
            session_id = session['id']
            lop_id = session['lop_id']
            admin_id = session.get('nguoi_chot_id')
            print(f"Processing session {session_id} for class {lop_id}...")

            # Lấy thống kê
            total_students_row = execute_one("SELECT COUNT(*) as count FROM sinh_vien WHERE lop_id = %s AND trang_thai = 1", (lop_id,))
            total_students = total_students_row['count'] if total_students_row else 0

            summary = get_session_attendance_summary(session_id)
            if not summary:
                summary = {"total_students": total_students, "present": 0, "late": 0,
                           "excused": 0, "unexcused": 0, "attendance_rate": 0,
                           "weighted_score_rate": 0, "records": []}

            snapshot_payload = {
                "session_id": session_id,
                "lop_id": lop_id,
                "closed_at": datetime.now().isoformat(),
                "closed_by": admin_id,
                "si_so_chot": summary.get("total_students", total_students),
                "summary": {
                    "total_students": summary.get("total_students", total_students),
                    "present": summary.get("present", 0),
                    "late": summary.get("late", 0),
                    "excused": summary.get("excused", 0),
                    "unexcused": summary.get("unexcused", 0),
                    "pending": summary.get("pending", 0),
                    "attendance_rate": summary.get("attendance_rate", 0),
                    "weighted_score_rate": summary.get("weighted_score_rate", 0),
                },
                "records": [
                    {
                        "sinh_vien_id": r.get("sinh_vien_id"),
                        "mssv": r.get("mssv", ""),
                        "ho_ten": r.get("ho_ten", ""),
                        "status": r.get("status", ""),
                        "display_status": r.get("display_status", ""),
                        "late_minutes": r.get("late_minutes", 0),
                        "method": r.get("method", ""),
                        "ghi_chu": r.get("ghi_chu", ""),
                        "thoi_gian": str(r.get("thoi_gian", "")),
                    }
                    for r in summary.get("records", [])
                ],
            }

            execute_update(
                "UPDATE phien_diem_danh SET ban_sao_bao_cao = %s WHERE id = %s",
                (json.dumps(snapshot_payload, ensure_ascii=False), session_id)
            )
            print(f"Generated snapshot for session {session_id}.")

        print("Completed generating missing snapshots.")
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    generate()
