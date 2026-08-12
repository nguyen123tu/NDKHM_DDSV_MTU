"""
Service: Quản lý vòng đời phiên điểm danh.
Hợp nhất Web Camera và Mobile App.
Đóng phiên = chốt trạng thái + tạo EXCUSED/UNEXCUSED + snapshot + audit log.
"""

import json
from datetime import datetime
from db.connection import execute_one, execute_update, execute_query, transaction
from config import Config
from services.attendance_policy import AttendanceStatus, get_session_attendance_summary

def _to_dict_list(cursor):
    if not cursor.description: return []
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def _to_dict_one(cursor):
    if not cursor.description: return None
    row = cursor.fetchone()
    if not row: return None
    cols = [col[0] for col in cursor.description]
    return dict(zip(cols, row))


class AttendanceSessionService:
    """
    Dịch vụ quản lý vòng đời của phiên điểm danh (Web Camera và Mobile).
    Đảm bảo tính hợp nhất, chốt dữ liệu transaction và thống kê chính xác.
    """

    @staticmethod
    def create_session(
        lop_id,
        admin_id=None,
        loai_phien="MOBILE",
        mo_ta=None,
        gio_hoc_du_kien=None,
        mo_checkin=None,
        dong_checkin=None,
        het_han=None,
        vi_do=None,
        kinh_do=None,
        radius=100,
        require_gps=False,
    ):
        """Tạo mới một phiên điểm danh hợp nhất (Web Camera / Mobile App)"""
        # Kiểm tra lớp học
        lop = execute_one(
            "SELECT id, ma_lop, ten_lop FROM lop_hoc WHERE id = %s", (lop_id,)
        )
        if not lop:
            return None, "Lớp học không tồn tại"

        # Nếu thiếu giờ dự kiến, thử lấy từ lịch học hoặc dùng thời điểm hiện tại
        now_dt = datetime.now()
        if not gio_hoc_du_kien:
            gio_hoc_du_kien = now_dt

        sql = """
            INSERT INTO phien_diem_danh (
                lop_id, admin_id, loai_phien, trang_thai, mo_ta,
                gio_hoc_du_kien, mo_checkin, dong_checkin, bat_dau, het_han,
                vi_do, kinh_do, radius, require_gps
            )
            OUTPUT INSERTED.id
            VALUES (%s, %s, %s, 1, %s, %s, %s, %s, GETDATE(), %s, %s, %s, %s, %s)
        """
        params = (
            lop_id,
            admin_id,
            loai_phien,
            mo_ta,
            gio_hoc_du_kien,
            mo_checkin,
            dong_checkin,
            het_han,
            vi_do,
            kinh_do,
            radius or 100,
            1 if require_gps else 0,
        )
        try:
            with transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(sql.replace('%s', '?'), params)
                inserted = cursor.fetchone()
                if not inserted:
                    return None, "Không thể lấy ID phiên điểm danh mới tạo"
                new_id = inserted[0]

                cursor.execute("SELECT * FROM phien_diem_danh WHERE id = ?", (new_id,))
                session = _to_dict_one(cursor)
                return session, None
        except Exception as e:
            error_str = str(e)
            if (
                "idx_unique_active_session" in error_str
                or "UNIQUE KEY" in error_str
                or "Violation of UNIQUE KEY constraint" in error_str
            ):
                return None, f"Lớp {lop['ma_lop']} đã có phiên điểm danh đang mở."
            print(f"[SESSION ERROR] create_session failed: {e}")
            return None, "Không thể tạo phiên điểm danh (Lỗi hệ thống)"

    @staticmethod
    def get_active_session(lop_id=None, session_id=None):
        """Lấy thông tin phiên điểm danh đang mở hợp lệ"""
        if session_id:
            row = execute_one(
                "SELECT * FROM phien_diem_danh WHERE id = %s AND trang_thai = 1 AND ISNULL(is_cancelled, 0) = 0",
                (session_id,),
            )
        elif lop_id:
            row = execute_one(
                "SELECT TOP 1 * FROM phien_diem_danh WHERE lop_id = %s AND trang_thai = 1 AND ISNULL(is_cancelled, 0) = 0 ORDER BY id DESC",
                (lop_id,),
            )
        else:
            return None

        if not row:
            return None

        # Kiểm tra hết hạn theo het_han hoặc dong_checkin
        now_dt = datetime.now()
        expire_dt = row.get("het_han") or row.get("dong_checkin")
        if expire_dt and hasattr(expire_dt, "year") and now_dt > expire_dt:
            # Tự động đóng nếu quá giờ và chốt dữ liệu
            AttendanceSessionService.close_session(row["id"], admin_id=None)
            return None

        return row

    @staticmethod
    def close_session(session_id, admin_id=None):
        """
        Đóng phiên điểm danh:
        1. Khóa phiên, ghi nhận ket_thuc, thoi_gian_chot, nguoi_chot_id.
        2. Chốt các bản ghi đã check-in hợp lệ (PRESENT / LATE).
        3. Ghép Đơn xin phép đã duyệt thành EXCUSED_ABSENCE.
        4. Tạo UNEXCUSED_ABSENCE cho sinh viên vắng không phép.
        5. Ghi audit log cho mỗi bản ghi tự động tạo.
        6. Tính toán và lưu Snapshot báo cáo (JSON) cùng si_so_chot.
        """
        session_row = execute_one(
            "SELECT * FROM phien_diem_danh WHERE id = %s", (session_id,)
        )
        if not session_row:
            return {"success": False, "message": "Phiên điểm danh không tồn tại"}

        if session_row["trang_thai"] == 0:
            return {
                "success": False,
                "message": "Phiên điểm danh đã được đóng trước đó",
            }

        if session_row.get("is_cancelled"):
            return {"success": False, "message": "Phiên điểm danh đã bị hủy"}

        lop_id = session_row["lop_id"]

        # Gộp tất cả thay đổi dữ liệu vào một transaction
        try:
            with transaction() as conn:
                cursor = conn.cursor()

                # 1. Khóa trạng thái phiên
                cursor.execute(
                    """
                    UPDATE phien_diem_danh
                    SET trang_thai = 0, ket_thuc = GETDATE(),
                        nguoi_chot_id = ?, thoi_gian_chot = GETDATE()
                    WHERE id = ?
                    """,
                    (admin_id, session_id),
                )

                # 2. Lấy danh sách toàn bộ sinh viên trong lớp
                cursor.execute(
                    "SELECT id, mssv, ho_ten, avatar, email FROM sinh_vien WHERE lop_id = ? AND trang_thai = 1 ORDER BY mssv ASC",
                    (lop_id,),
                )
                students = _to_dict_list(cursor)
                total_students = len(students)

                # 3. Lấy các bản ghi đã điểm danh trong phiên này
                cursor.execute(
                    """
                    SELECT id, sinh_vien_id, status, trang_thai, late_minutes, thoi_gian, gio_vao_lop, do_chinh_xac, method, ghi_chu
                    FROM diem_danh WHERE phien_id = ?
                    """,
                    (session_id,),
                )
                attended_map = {rec["sinh_vien_id"]: rec for rec in _to_dict_list(cursor)}

                # 4. Tìm các đơn xin phép đã được duyệt (trang_thai = 1) VÀ thuộc phiên này
                cursor.execute(
                    """
                    SELECT id, sinh_vien_id, ly_do
                    FROM don_xin_phep
                    WHERE lop_id = ? AND phien_id = ? AND trang_thai = 1
                    """,
                    (lop_id, session_id),
                )
                approved_leave_map = {
                    req["sinh_vien_id"]: req for req in _to_dict_list(cursor)
                }

                # 5. Xử lý bổ sung cho sinh viên chưa có bản ghi
                for sv in students:
                    sv_id = sv["id"]
                    if sv_id in attended_map:
                        continue

                    if sv_id in approved_leave_map:
                        # Tạo bản ghi EXCUSED_ABSENCE
                        req = approved_leave_map[sv_id]
                        note = f"Vắng có phép (Đã duyệt đơn: {req['ly_do']})"
                        cursor.execute(
                            """
                            INSERT INTO diem_danh (
                                phien_id, sinh_vien_id, lop_id, trang_thai, status, late_minutes, method, ghi_chu
                            )
                            OUTPUT INSERTED.id
                            VALUES (?, ?, ?, ?, ?, 0, 'LEAVE_REQUEST', ?)
                            """,
                            (
                                session_id,
                                sv_id,
                                lop_id,
                                AttendanceStatus.display(
                                    AttendanceStatus.EXCUSED_ABSENCE
                                ),
                                AttendanceStatus.EXCUSED_ABSENCE,
                                note,
                            ),
                        )
                        inserted_rec = cursor.fetchone()
                        if inserted_rec:
                            cursor.execute(
                                """
                                INSERT INTO attendance_audit_log (attendance_id, old_status, new_status, changed_by, reason)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    inserted_rec[0],
                                    None,
                                    AttendanceStatus.EXCUSED_ABSENCE,
                                    admin_id,
                                    f"Tự động tạo khi đóng phiên: {note}",
                                ),
                            )
                    else:
                        # Tạo bản ghi UNEXCUSED_ABSENCE
                        cursor.execute(
                            """
                            INSERT INTO diem_danh (
                                phien_id, sinh_vien_id, lop_id, trang_thai, status, late_minutes, method, ghi_chu
                            )
                            OUTPUT INSERTED.id
                            VALUES (?, ?, ?, ?, ?, 0, 'SYSTEM_AUTO', ?)
                            """,
                            (
                                session_id,
                                sv_id,
                                lop_id,
                                AttendanceStatus.display(
                                    AttendanceStatus.UNEXCUSED_ABSENCE
                                ),
                                AttendanceStatus.UNEXCUSED_ABSENCE,
                                "Vắng không phép",
                            ),
                        )
                        inserted_rec = cursor.fetchone()
                        if inserted_rec:
                            cursor.execute(
                                """
                                INSERT INTO attendance_audit_log (attendance_id, old_status, new_status, changed_by, reason)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    inserted_rec[0],
                                    None,
                                    AttendanceStatus.UNEXCUSED_ABSENCE,
                                    admin_id,
                                    "Tự động tạo khi đóng phiên: Vắng không phép",
                                ),
                            )

                # 6. Tự tính lại thống kê trong transaction (thay vì gọi hàm bên ngoài)
                cursor.execute(
                    """SELECT d.*, sv.mssv, sv.ho_ten, sv.avatar
                       FROM diem_danh d
                       JOIN sinh_vien sv ON d.sinh_vien_id = sv.id
                       WHERE d.phien_id = ?
                       ORDER BY sv.mssv ASC""",
                    (session_id,),
                )
                dd_records = _to_dict_list(cursor)

                counts = {s: 0 for s in AttendanceStatus.ALL}
                records = []
                for r in dd_records:
                    st = r.get("status") or AttendanceStatus.PRESENT
                    if st in counts:
                        counts[st] += 1
                    else:
                        counts[AttendanceStatus.UNEXCUSED_ABSENCE] += 1

                    records.append(
                        {
                            "attendance_id": r.get("id"),
                            "sinh_vien_id": r.get("sinh_vien_id"),
                            "mssv": r.get("mssv", ""),
                            "ho_ten": r.get("ho_ten", ""),
                            "status": st,
                            "display_status": AttendanceStatus.display(st),
                            "late_minutes": r.get("late_minutes", 0),
                            "method": r.get("method", ""),
                            "ghi_chu": r.get("ghi_chu", ""),
                            "thoi_gian": str(r.get("thoi_gian", "")),
                        }
                    )

                si_so_chot = total_students
                present_count = counts[AttendanceStatus.PRESENT]
                late_count = counts[AttendanceStatus.LATE]
                excused_count = counts[AttendanceStatus.EXCUSED_ABSENCE]
                unexcused_count = counts[AttendanceStatus.UNEXCUSED_ABSENCE]

                attendance_rate = (
                    (present_count + late_count) / max(1, si_so_chot)
                ) * 100
                w_p = getattr(Config, "WEIGHT_PRESENT", 1.0)
                w_l = getattr(Config, "WEIGHT_LATE", 0.75)
                w_e = getattr(Config, "WEIGHT_EXCUSED", 1.0)
                weighted = present_count * w_p + late_count * w_l + excused_count * w_e
                weighted_score_rate = (weighted / max(1, si_so_chot)) * 100

                snapshot_payload = {
                    "session_id": session_id,
                    "lop_id": lop_id,
                    "closed_at": datetime.now().isoformat(),
                    "closed_by": admin_id,
                    "si_so_chot": si_so_chot,
                    "summary": {
                        "total_students": si_so_chot,
                        "present": present_count,
                        "late": late_count,
                        "excused": excused_count,
                        "unexcused": unexcused_count,
                        "pending": counts[AttendanceStatus.PENDING_REVIEW],
                        "attendance_rate": round(attendance_rate, 2),
                        "weighted_score_rate": round(weighted_score_rate, 2),
                    },
                    "records": records,
                }

                # 7. Lưu báo cáo vào phien_diem_danh
                cursor.execute(
                    "UPDATE phien_diem_danh SET si_so_chot = ?, ban_sao_bao_cao = ? WHERE id = ?",
                    (
                        si_so_chot,
                        json.dumps(snapshot_payload, ensure_ascii=False),
                        session_id,
                    ),
                )

        except Exception as e:
            return {"success": False, "message": f"Lỗi trong quá trình đóng phiên: {e}"}

        return {
            "success": True,
            "message": "Đã đóng phiên và chốt dữ liệu chuyên cần thành công",
            "session_id": session_id,
            "summary": snapshot_payload["summary"],
            "records": snapshot_payload["records"],
        }

    @staticmethod
    def cancel_session(session_id, admin_id=None, reason=""):
        """
        Hủy phiên điểm danh (soft-cancel). Không xóa cứng.
        Dữ liệu vẫn giữ nguyên trong DB nhưng phiên được đánh dấu là đã hủy.
        """
        session_row = execute_one(
            "SELECT * FROM phien_diem_danh WHERE id = %s", (session_id,)
        )
        if not session_row:
            return {"success": False, "message": "Phiên điểm danh không tồn tại"}

        execute_update(
            """
            UPDATE phien_diem_danh
            SET trang_thai = 0, is_cancelled = 1,
                cancelled_by = %s, cancelled_at = GETDATE(), cancel_reason = %s
            WHERE id = %s
            """,
            (admin_id, reason, session_id),
        )

        return {
            "success": True,
            "message": f"Đã hủy phiên điểm danh #{session_id}",
            "session_id": session_id,
        }

    @staticmethod
    def update_attendance_status(attendance_id, new_status, admin_id, reason):
        """
        Giảng viên sửa trạng thái điểm danh. Bắt buộc nhập lý do.
        Ghi audit log.
        """
        if not reason or not reason.strip():
            return {
                "success": False,
                "message": "Bắt buộc nhập lý do khi sửa trạng thái điểm danh",
            }

        if new_status not in AttendanceStatus.ALL:
            return {
                "success": False,
                "message": f"Trạng thái '{new_status}' không hợp lệ",
            }

        record = execute_one(
            "SELECT id, status, phien_id, sinh_vien_id FROM diem_danh WHERE id = %s",
            (attendance_id,),
        )
        if not record:
            return {"success": False, "message": "Bản ghi điểm danh không tồn tại"}

        old_status = record.get("status", "UNKNOWN")

        # Cập nhật trạng thái
        execute_update(
            """
            UPDATE diem_danh
            SET status = %s, trang_thai = %s,
                verified_by = %s, updated_reason = %s
            WHERE id = %s
            """,
            (
                new_status,
                AttendanceStatus.display(new_status),
                admin_id,
                reason,
                attendance_id,
            ),
        )

        # Ghi audit log
        execute_update(
            """
            INSERT INTO attendance_audit_log (attendance_id, old_status, new_status, changed_by, reason)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (attendance_id, old_status, new_status, admin_id, reason),
        )

        return {
            "success": True,
            "message": f"Đã cập nhật trạng thái từ {AttendanceStatus.display(old_status)} → {AttendanceStatus.display(new_status)}",
            "old_status": old_status,
            "new_status": new_status,
        }

    @staticmethod
    def get_session_details(session_id):
        """Lấy chi tiết phiên điểm danh kèm thống kê từ DB hoặc Snapshot đã chốt"""
        session_row = execute_one(
            "SELECT p.*, l.ten_lop, l.ma_lop FROM phien_diem_danh p JOIN lop_hoc l ON p.lop_id = l.id WHERE p.id = %s",
            (session_id,),
        )
        if not session_row:
            return None

        # Nếu đã có snapshot báo cáo
        if session_row.get("ban_sao_bao_cao"):
            try:
                snapshot = json.loads(session_row["ban_sao_bao_cao"])
                session_row["snapshot"] = snapshot
            except Exception:
                pass

        return session_row


def _log_auto_audit(session_id, sv_id, new_status, admin_id, reason):
    """Ghi audit log cho các bản ghi tự động tạo khi đóng phiên."""
    try:
        # Lấy ID bản ghi vừa insert
        record = execute_one(
            "SELECT TOP 1 id FROM diem_danh WHERE phien_id = %s AND sinh_vien_id = %s ORDER BY id DESC",
            (session_id, sv_id),
        )
        if record:
            execute_update(
                """
                INSERT INTO attendance_audit_log (attendance_id, old_status, new_status, changed_by, reason)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (record["id"], None, new_status, admin_id, reason),
            )
    except Exception as e:
        # Fallback lưu log ra file nếu DB lỗi
        import os, json, datetime
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            with open(os.path.join(log_dir, "audit_fallback.log"), "a", encoding="utf-8") as f:
                log_entry = {
                    "time": datetime.datetime.now().isoformat(),
                    "session_id": session_id,
                    "sv_id": sv_id,
                    "new_status": new_status,
                    "admin_id": admin_id,
                    "reason": reason,
                    "error": str(e)
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except:
            pass
