"""
Test Suite: Kiểm thử hệ thống điểm danh MTUFace.
Chạy: python -m pytest tests/test_attendance.py -v
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Thêm project root vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAttendancePolicy(unittest.TestCase):
    """Kiểm thử module attendance_policy."""

    def test_compute_status_present(self):
        """Đúng giờ → PRESENT."""
        from services.attendance_policy import compute_status, AttendanceStatus

        scheduled = datetime(2026, 7, 30, 7, 0)
        checkin = datetime(2026, 7, 30, 7, 5)  # 5 phút sau (trong grace)
        status, late = compute_status(checkin, scheduled, grace_period=15)
        self.assertEqual(status, AttendanceStatus.PRESENT)
        self.assertEqual(late, 0)

    def test_compute_status_late(self):
        """Đi trễ → LATE."""
        from services.attendance_policy import compute_status, AttendanceStatus

        scheduled = datetime(2026, 7, 30, 7, 0)
        checkin = datetime(2026, 7, 30, 7, 20)  # 20 phút sau
        status, late = compute_status(checkin, scheduled, grace_period=15)
        self.assertEqual(status, AttendanceStatus.LATE)
        self.assertEqual(late, 20)

    def test_compute_status_early(self):
        """Đến sớm → PRESENT."""
        from services.attendance_policy import compute_status, AttendanceStatus

        scheduled = datetime(2026, 7, 30, 7, 0)
        checkin = datetime(2026, 7, 30, 6, 50)
        status, late = compute_status(checkin, scheduled, grace_period=15)
        self.assertEqual(status, AttendanceStatus.PRESENT)
        self.assertEqual(late, 0)

    def test_compute_status_no_scheduled_start(self):
        """Không có giờ dự kiến → PRESENT."""
        from services.attendance_policy import compute_status, AttendanceStatus

        status, late = compute_status(datetime.now(), None)
        self.assertEqual(status, AttendanceStatus.PRESENT)
        self.assertEqual(late, 0)

    def test_validate_gps_in_range(self):
        """GPS trong bán kính → valid."""
        from services.attendance_policy import validate_gps

        # 2 điểm cách nhau ~50m
        valid, dist = validate_gps(10.8505, 106.7725, 10.8505, 106.7730, radius=100)
        self.assertTrue(valid)

    def test_validate_gps_out_of_range(self):
        """GPS ngoài bán kính → invalid."""
        from services.attendance_policy import validate_gps

        # 2 điểm cách nhau ~1km
        valid, dist = validate_gps(10.8505, 106.7725, 10.8600, 106.7725, radius=100)
        self.assertFalse(valid)
        self.assertGreater(dist, 100)

    def test_validate_gps_missing_student_coords(self):
        """Thiếu GPS sinh viên → invalid."""
        from services.attendance_policy import validate_gps

        valid, dist = validate_gps(None, None, 10.8505, 106.7725, radius=100)
        self.assertFalse(valid)

    def test_validate_gps_missing_session_coords(self):
        """Thiếu GPS phiên → bypass (valid)."""
        from services.attendance_policy import validate_gps

        valid, dist = validate_gps(10.8505, 106.7725, None, None, radius=100)
        self.assertTrue(valid)

    def test_attendance_status_display(self):
        """Hiển thị tiếng Việt."""
        from services.attendance_policy import AttendanceStatus

        self.assertEqual(AttendanceStatus.display("PRESENT"), "Có mặt")
        self.assertEqual(AttendanceStatus.display("LATE"), "Đi trễ")
        self.assertEqual(AttendanceStatus.display("EXCUSED_ABSENCE"), "Vắng có phép")

    def test_attendance_status_symbol(self):
        """Ký hiệu báo cáo."""
        from services.attendance_policy import AttendanceStatus

        self.assertEqual(AttendanceStatus.symbol("PRESENT"), "P")
        self.assertEqual(AttendanceStatus.symbol("LATE"), "L")
        self.assertEqual(AttendanceStatus.symbol("UNEXCUSED_ABSENCE"), "A")


class TestRecordAttendance(unittest.TestCase):
    """Kiểm thử hàm record_attendance()."""

    @patch("services.attendance_service.execute_one")
    def test_missing_session(self, mock_exec):
        """Thiếu session_id → MISSING_SESSION."""
        from services.attendance_service import record_attendance

        result = record_attendance(session_id=None, student_id=1, method="FACE_CAMERA")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "MISSING_SESSION")

    @patch("services.attendance_service.execute_one")
    def test_session_not_found(self, mock_exec):
        """Phiên không tồn tại."""
        mock_exec.return_value = None
        from services.attendance_service import record_attendance

        result = record_attendance(session_id=999, student_id=1, method="FACE_CAMERA")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "SESSION_NOT_FOUND")

    @patch("services.attendance_service.execute_one")
    def test_session_closed(self, mock_exec):
        """Phiên đã đóng."""
        mock_exec.return_value = {"trang_thai": 0, "is_cancelled": 0, "lop_id": 1}
        from services.attendance_service import record_attendance

        result = record_attendance(session_id=1, student_id=1, method="FACE_CAMERA")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "SESSION_CLOSED")

    @patch("services.attendance_service.execute_update")
    @patch("services.attendance_service.execute_one")
    def test_student_wrong_class(self, mock_exec_one, mock_exec_update):
        """Sinh viên khác lớp."""
        # Phiên tồn tại, lop_id = 1
        mock_exec_one.side_effect = [
            {
                "id": 1,
                "trang_thai": 1,
                "is_cancelled": 0,
                "lop_id": 1,
                "het_han": None,
                "dong_checkin": None,
                "require_gps": 0,
            },
            {"id": 5, "mssv": "SV001", "lop_id": 2, "ho_ten": "Test", "is_locked": 0},
        ]
        from services.attendance_service import record_attendance

        result = record_attendance(session_id=1, student_id=5, method="FACE_CAMERA")
        self.assertFalse(result["success"])
        self.assertEqual(result["error_code"], "WRONG_CLASS")


class TestAttendanceSessionService(unittest.TestCase):
    """Kiểm thử service vòng đời phiên."""

    @patch("services.attendance_session_service.execute_one")
    def test_close_nonexistent_session(self, mock_exec):
        """Đóng phiên không tồn tại."""
        mock_exec.return_value = None
        from services.attendance_session_service import AttendanceSessionService

        result = AttendanceSessionService.close_session(999)
        self.assertFalse(result["success"])

    @patch("services.attendance_session_service.execute_one")
    def test_close_already_closed(self, mock_exec):
        """Đóng phiên đã đóng."""
        mock_exec.return_value = {
            "id": 1,
            "trang_thai": 0,
            "is_cancelled": 0,
            "lop_id": 1,
        }
        from services.attendance_session_service import AttendanceSessionService

        result = AttendanceSessionService.close_session(1)
        self.assertFalse(result["success"])

    def test_update_status_without_reason(self):
        """Sửa trạng thái không nhập lý do → từ chối."""
        from services.attendance_session_service import AttendanceSessionService

        result = AttendanceSessionService.update_attendance_status(1, "PRESENT", 1, "")
        self.assertFalse(result["success"])

    def test_update_status_invalid_status(self):
        """Trạng thái không hợp lệ."""
        from services.attendance_session_service import AttendanceSessionService

        result = AttendanceSessionService.update_attendance_status(
            1, "INVALID_STATUS", 1, "Test reason"
        )
        self.assertFalse(result["success"])

    @patch("services.attendance_session_service.execute_one")
    def test_cancel_nonexistent_session(self, mock_exec):
        """Hủy phiên không tồn tại."""
        mock_exec.return_value = None
        from services.attendance_session_service import AttendanceSessionService

        result = AttendanceSessionService.cancel_session(999)
        self.assertFalse(result["success"])

    @patch("services.attendance_session_service.execute_update")
    @patch("services.attendance_session_service.execute_one")
    def test_cancel_existing_session(self, mock_exec_one, mock_exec_update):
        """Hủy phiên thành công → soft cancel."""
        mock_exec_one.return_value = {"id": 1, "trang_thai": 1, "lop_id": 1}
        mock_exec_update.return_value = 1
        from services.attendance_session_service import AttendanceSessionService

        result = AttendanceSessionService.cancel_session(1, admin_id=1, reason="Test")
        self.assertTrue(result["success"])


if __name__ == "__main__":
    unittest.main()
