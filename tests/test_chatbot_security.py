"""Kiểm thử các hàng rào bảo mật và định danh hội thoại chatbot."""

import os
import sys
import unittest
from unittest.mock import patch

from flask import Flask, session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChatbotConversationId(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-only"

    def test_conversation_is_namespaced_by_user(self):
        from routes.chatbot import _web_conversation_id

        with self.app.test_request_context("/chatbot/ask"):
            session["admin_id"] = 12
            result = _web_conversation_id({"conversation_id": "c_123"})

        self.assertEqual(result, "web_12_c_123")

    def test_rejects_invalid_conversation_id(self):
        from routes.chatbot import _web_conversation_id

        with self.app.test_request_context("/chatbot/ask"):
            session["admin_id"] = 12
            with self.assertRaises(ValueError):
                _web_conversation_id({"conversation_id": "../../other-user"})

    def test_ask_requires_web_login(self):
        from routes.chatbot import chatbot_bp

        self.app.register_blueprint(chatbot_bp)
        response = self.app.test_client().post(
            "/chatbot/ask", json={"question": "Xin chào"}
        )

        self.assertEqual(response.status_code, 401)


class TestChatbotToolAuthorization(unittest.TestCase):
    @patch("services.ai_tools._tool_get_student_info")
    def test_student_cannot_query_another_student(self, mock_lookup):
        from services.ai_tools import execute_tool

        result = execute_tool(
            {"name": "get_student_info", "arguments": '{"mssv":"SV002"}'},
            user_context={"role": "student", "username": "SV001"},
        )

        self.assertIn("chính mình", result)
        mock_lookup.assert_not_called()

    @patch("services.ai_tools._tool_export_report")
    def test_student_cannot_export_report(self, mock_export):
        from services.ai_tools import execute_tool

        result = execute_tool(
            {
                "name": "export_attendance_report",
                "arguments": '{"ma_lop":"CNTT1","format":"excel"}',
            },
            user_context={"role": "student", "username": "SV001"},
        )

        self.assertIn("không có quyền", result)
        mock_export.assert_not_called()


if __name__ == "__main__":
    unittest.main()
