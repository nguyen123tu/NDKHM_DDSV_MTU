"""
AI Chatbot Service — Trợ lý AI thông minh cho hệ thống MTUFace
Sử dụng RAG (Retrieval-Augmented Generation) để trả lời câu hỏi
dựa trên kiến thức toàn bộ dự án.

Hỗ trợ LLM Backend:
- NVIDIA NIM API (cấu hình qua biến môi trường)
"""

import os
import json
import time
import threading
import requests
import base64
from datetime import datetime
from config import Config
from services.ai_tools import TOOLS_SCHEMA, execute_tool

# ─── SYSTEM PROMPT ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """Bạn là **MTU AI Assistant** — trợ lý AI thông minh của hệ thống "Điểm danh Thông minh bằng Nhận diện Khuôn mặt" (MTUFace) tại Trường Đại học Xây Dựng Miền Tây.

## Vai trò:
- Bạn hiểu sâu về toàn bộ hệ thống: kiến trúc Flask MVC, AI Engine (InsightFace/ArcFace/DeepFace), database MySQL, WebSocket realtime, mobile API.
- Bạn trả lời các câu hỏi về hệ thống, hướng dẫn sử dụng, giải thích code, debug lỗi.
- Bạn nói tiếng Việt tự nhiên, thân thiện nhưng chuyên nghiệp.

## Quy tắc:
1. Trả lời DỰA TRÊN kiến thức dự án được cung cấp trong context bên dưới.
2. Nếu câu hỏi nằm ngoài phạm vi dự án, hãy cho biết và gợi ý hướng tìm kiếm. Riêng các câu hỏi về chào hỏi, ngày tháng, thời gian hiện tại thì bạn ĐƯỢC PHÉP trả lời bình thường.
3. Khi trích dẫn code, hãy chỉ rõ file nguồn.
4. Sử dụng markdown formatting cho câu trả lời rõ ràng.
5. Nếu không chắc chắn, hãy nói rõ thay vì bịa ra thông tin.

## Thông tin hệ thống:
- Tên: Hệ thống Điểm danh Thông minh MTUFace
- Backend: Python Flask + SocketIO + Eventlet
- AI: InsightFace (SCRFD + ArcFace 512-d) / DeepFace / YOLO+ResNet
- Database: Microsoft SQL Server (pymssql)
- Frontend: Jinja2 + Tailwind CSS + JavaScript
- Mobile: Flutter (REST API + JWT Auth)
- Alerts: Telegram Bot
"""


class AIChatbot:
    """
    AI Chatbot sử dụng RAG pipeline
    """

    def __init__(self):
        self._lock = threading.Lock()

        # Khóa bí mật chỉ được lấy từ môi trường, tuyệt đối không ghi trong source.
        self._nvidia_key = Config.NVIDIA_API_KEY

    def _require_nvidia_key(self):
        if not self._nvidia_key:
            raise RuntimeError(
                "Thiếu NVIDIA_API_KEY. Hãy cấu hình khóa trong file .env rồi khởi động lại server."
            )

    def chat(
        self, question: str, session_id: str = "default", user_context: dict = None
    ) -> dict:
        start_time = time.time()

        if question.strip().startswith("/search "):
            question = question.strip()[8:].strip()

        try:
            # Inject Realtime Context
            now = datetime.now()
            weekdays = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
            weekday_vn = weekdays[now.weekday()]
            context = f"Thời gian hệ thống hiện tại: {weekday_vn}, ngày {now.strftime('%d/%m/%Y %H:%M:%S')}. Hãy luôn dùng thông tin này để trả lời chính xác nếu người dùng hỏi về ngày, giờ, hoặc thứ hiện tại.\n"
            if user_context:
                from db.connection import execute_one

                role = user_context.get("role")
                username = user_context.get("username")

                if role == "student":
                    sv = execute_one(
                        "SELECT * FROM sinh_vien WHERE mssv = %s", (username,)
                    )
                    if sv:
                        lop = execute_one(
                            "SELECT ten_lop FROM lop_hoc WHERE id = %s", (sv["lop_id"],)
                        )
                        ten_lop = lop["ten_lop"] if lop else "Không rõ"

                        total_sessions = execute_one(
                            "SELECT COUNT(*) as count FROM phien_diem_danh WHERE lop_id = %s",
                            (sv["lop_id"],),
                        )
                        present = execute_one(
                            "SELECT COUNT(*) as count FROM diem_danh WHERE sinh_vien_id = %s AND status IN ('PRESENT', 'LATE')",
                            (sv["id"],),
                        )
                        vang = (total_sessions["count"] if total_sessions else 0) - (
                            present["count"] if present else 0
                        )
                        if vang < 0:
                            vang = 0

                        realtime_info = (
                            f"\n\n--- THÔNG TIN SINH VIÊN ĐANG CHAT (REALTIME) ---\n"
                            f"- Vai trò: Sinh viên\n"
                            f"- Họ tên: {sv['ho_ten']}\n"
                            f"- MSSV: {sv['mssv']}\n"
                            f"- Lớp: {ten_lop}\n"
                            f"- Tổng số buổi đã vắng: {vang}\n"
                            f"-> Yêu cầu: Hãy dùng thông tin này để xưng hô (ví dụ: Chào bạn Nguyễn Văn A) và trả lời chính xác nếu sinh viên hỏi về số buổi vắng của họ."
                        )
                        context += realtime_info
                else:
                    admin = execute_one(
                        "SELECT * FROM admin WHERE username = %s", (username,)
                    )
                    if admin:
                        admin_role_name = (
                            "Giảng viên"
                            if admin["role"] == "lecturer"
                            else "Quản trị viên"
                        )
                        realtime_info = (
                            f"\n\n--- THÔNG TIN NGƯỜI DÙNG ĐANG CHAT (REALTIME) ---\n"
                            f"- Vai trò: {admin_role_name}\n"
                            f"- Họ tên: {admin['ho_ten']}\n"
                            f"- Tài khoản: {admin['username']}\n"
                            f"-> Yêu cầu: Hãy dùng thông tin này để xưng hô (ví dụ: Chào thầy/cô {admin['ho_ten']}) và hỗ trợ tận tình."
                        )
                        context += realtime_info

            history = self._get_history(session_id)

            # Gọi NVIDIA API (Sync) với Tool Calling
            answer = self._call_nvidia(
                question, context, history, session_id, user_context=user_context
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "answer": answer,
                "sources": [],  # Bỏ sources cố định, Tool search_knowledge sẽ lo việc này
                "duration_ms": duration_ms,
                "backend": "nvidia",
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "answer": f"❌ Lỗi khi gọi AI NVIDIA: {str(e)}",
                "sources": [],
                "duration_ms": duration_ms,
                "backend": "nvidia",
                "error": True,
            }

    def chat_stream(
        self, question: str, session_id: str = "default", user_context: dict = None
    ):
        start_time = time.time()

        if question.strip().startswith("/search "):
            question = question.strip()[8:].strip()

        try:
            now = datetime.now()
            weekdays = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
            weekday_vn = weekdays[now.weekday()]
            context = f"Thời gian hệ thống hiện tại: {weekday_vn}, ngày {now.strftime('%d/%m/%Y %H:%M:%S')}. Hãy luôn dùng thông tin này để trả lời chính xác nếu người dùng hỏi về ngày, giờ, hoặc thứ hiện tại.\n"
            if user_context:
                from db.connection import execute_one

                role = user_context.get("role")
                username = user_context.get("username")

                if role == "student":
                    sv = execute_one(
                        "SELECT * FROM sinh_vien WHERE mssv = %s", (username,)
                    )
                    if sv:
                        lop = execute_one(
                            "SELECT ten_lop FROM lop_hoc WHERE id = %s", (sv["lop_id"],)
                        )
                        ten_lop = lop["ten_lop"] if lop else "Không rõ"

                        total_sessions = execute_one(
                            "SELECT COUNT(*) as count FROM phien_diem_danh WHERE lop_id = %s",
                            (sv["lop_id"],),
                        )
                        present = execute_one(
                            "SELECT COUNT(*) as count FROM diem_danh WHERE sinh_vien_id = %s AND status IN ('PRESENT', 'LATE')",
                            (sv["id"],),
                        )
                        vang = (total_sessions["count"] if total_sessions else 0) - (
                            present["count"] if present else 0
                        )
                        if vang < 0:
                            vang = 0

                        realtime_info = (
                            f"\n\n--- THÔNG TIN SINH VIÊN ĐANG CHAT (REALTIME) ---\n"
                            f"- Vai trò: Sinh viên\n"
                            f"- Họ tên: {sv['ho_ten']}\n"
                            f"- MSSV: {sv['mssv']}\n"
                            f"- Lớp: {ten_lop}\n"
                            f"- Tổng số buổi đã vắng: {vang}\n"
                            f"-> Hướng dẫn: Hãy dùng tên của người dùng để xưng hô. NẾU họ hỏi về số buổi vắng, hãy dùng con số trên để trả lời."
                        )
                        context += realtime_info
                else:
                    admin = execute_one(
                        "SELECT * FROM admin WHERE username = %s", (username,)
                    )
                    if admin:
                        admin_role_name = (
                            "Giảng viên"
                            if admin["role"] == "lecturer"
                            else "Quản trị viên"
                        )
                        realtime_info = (
                            f"\n\n--- THÔNG TIN NGƯỜI DÙNG ĐANG CHAT (REALTIME) ---\n"
                            f"- Vai trò: {admin_role_name}\n"
                            f"- Họ tên: {admin['ho_ten']}\n"
                            f"- Tài khoản: {admin['username']}\n"
                            f"-> Yêu cầu: Hãy dùng thông tin này để xưng hô (ví dụ: Chào thầy/cô {admin['ho_ten']}) và hỗ trợ tận tình."
                        )
                        context += realtime_info

            history = self._get_history(session_id)

            # Khởi tạo stream không sources trước
            yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"

            # Gọi NVIDIA API Stream
            for chunk in self._call_nvidia_stream(
                question,
                context,
                history,
                session_id,
                user_context=user_context,
            ):
                yield chunk

            duration_ms = int((time.time() - start_time) * 1000)
            yield f"data: {json.dumps({'type': 'done', 'duration_ms': duration_ms})}\n\n"

        except Exception as e:
            error_text = f"Lỗi gọi AI NVIDIA: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'text': error_text})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'duration_ms': 0})}\n\n"

    def clear_history(self, session_id: str = "default"):
        from db.connection import execute_update
        try:
            execute_update("DELETE FROM chat_session WHERE id = %s", (session_id,))
        except:
            pass

    def get_suggested_questions(self) -> list:
        return [
            "Hệ thống điểm danh hoạt động như thế nào?",
            "Giải thích thuật toán ArcFace trong dự án",
            "Cấu trúc database gồm những bảng nào?",
            "Làm sao để train AI cho sinh viên mới?",
        ]

    def _build_context(self, chunks: list) -> str:
        if not chunks:
            return "(Không tìm thấy kiến thức liên quan trong kho dữ liệu)"
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"--- Nguồn {i}: {chunk['source']} ({chunk['category']}) ---\n"
                f"{chunk['text']}\n"
            )
        return "\n".join(parts)

    def _call_nvidia(
        self,
        question: str,
        context: str,
        history: list,
        session_id: str,
        user_context: dict = None,
    ) -> str:
        self._require_nvidia_key()
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[-6:]:
            # Filter out tool role messages from simple history just in case, or adapt it.
            # LLaMA 3.1 supports tool and function roles.
            messages.append(msg)

        user_prompt = f"{context}\n\n## Câu hỏi:\n{question}" if context else question
        self._add_to_history(session_id, {"role": "user", "content": user_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": "meta/llama-3.1-8b-instruct",
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.5,
            "top_p": 0.95,
            "stream": False,
            "tools": TOOLS_SCHEMA,
            "tool_choice": "auto",
        }

        headers = {
            "Authorization": f"Bearer {self._nvidia_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code != 200:
            raise ValueError(
                f"NVIDIA API Error ({response.status_code}): {response.text[:200]}"
            )

        data = response.json()
        message_obj = data["choices"][0]["message"]

        # Kiểm tra xem LLM có muốn gọi Tool không
        if message_obj.get("tool_calls"):
            self._add_to_history(session_id, message_obj)
            messages.append(message_obj)

            # Thực thi tất cả các tools được yêu cầu
            for tool_call in message_obj["tool_calls"]:
                tool_response = execute_tool(
                    tool_call["function"], user_context=user_context
                )
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_response,
                }
                self._add_to_history(session_id, tool_msg)
                messages.append(tool_msg)

            # Gọi API lần 2 sau khi có kết quả từ Tool
            payload["messages"] = messages
            # Bỏ tools ở lần gọi thứ 2 để nó trả lời luôn
            del payload["tools"]
            del payload["tool_choice"]

            response2 = requests.post(url, json=payload, headers=headers, timeout=60)
            if response2.status_code != 200:
                raise ValueError(
                    f"NVIDIA API Tool Res Error ({response2.status_code}): {response2.text[:200]}"
                )

            data2 = response2.json()
            final_content = data2["choices"][0]["message"]["content"]
            self._add_to_history(
                session_id, {"role": "assistant", "content": final_content}
            )
            return final_content
        else:
            # Không gọi tool, trả lời trực tiếp
            content = message_obj.get("content", "")
            self._add_to_history(session_id, {"role": "assistant", "content": content})
            return content

    def _call_nvidia_stream(
        self,
        question: str,
        context: str,
        history: list,
        session_id: str,
        user_context: dict = None,
    ):
        # Vì streaming tool_calls cần tích lũy chuỗi JSON khá phức tạp,
        # Cách tốt nhất là tái sử dụng logic _call_nvidia() sync bên trên, nhưng trả về stream fake ở đoạn cuối.
        # Hoặc, để đơn giản, ta fallback stream về _call_nvidia() (bất đồng bộ nội bộ) và stream chunk ra.
        self._require_nvidia_key()
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[-6:]:
            messages.append(msg)

        user_prompt = f"{context}\n\n## Câu hỏi:\n{question}" if context else question
        self._add_to_history(session_id, {"role": "user", "content": user_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": "meta/llama-3.1-8b-instruct",
            "messages": messages,
            "max_tokens": 4096,
            "temperature": 0.5,
            "top_p": 0.95,
            "stream": False,  # Tạm tắt stream để xử lý tool gọi nội bộ trước
            "tools": TOOLS_SCHEMA,
            "tool_choice": "auto",
        }

        headers = {
            "Authorization": f"Bearer {self._nvidia_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            # 1. Gọi API (Sync) để kiểm tra Tool Call
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code != 200:
                yield f"data: {json.dumps({'type': 'error', 'text': f'Lỗi NVIDIA API: {response.text[:200]}' })}\n\n"
                return

            data = response.json()
            message_obj = data["choices"][0]["message"]

            # 2. Nếu có Tool Call -> Thực thi -> Gọi API lần 2 với stream = True
            if message_obj.get("tool_calls"):
                tool_name = message_obj["tool_calls"][0]["function"]["name"]
                yield f"data: {json.dumps({'type': 'tool_call', 'tool_name': tool_name})}\n\n"

                self._add_to_history(session_id, message_obj)
                messages.append(message_obj)

                for tool_call in message_obj["tool_calls"]:
                    tool_response = execute_tool(
                        tool_call["function"], user_context=user_context
                    )
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_response,
                    }
                    self._add_to_history(session_id, tool_msg)
                    messages.append(tool_msg)

                payload["messages"] = messages
                payload["stream"] = True
                del payload["tools"]
                del payload["tool_choice"]

                # Gọi API Stream thực sự sau khi có tool result
                response_stream = requests.post(
                    url, json=payload, headers=headers, stream=True, timeout=120
                )
                full_answer = ""
                for line in response_stream.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                stream_data = json.loads(data_str)
                                if (
                                    "choices" in stream_data
                                    and len(stream_data["choices"]) > 0
                                ):
                                    delta = stream_data["choices"][0].get("delta", {})
                                    chunk_text = delta.get("content", "")
                                    if chunk_text:
                                        full_answer += chunk_text
                                        yield f"data: {json.dumps({'type': 'chunk', 'text': chunk_text})}\n\n"
                            except Exception:
                                pass
                self._add_to_history(
                    session_id, {"role": "assistant", "content": full_answer}
                )

            else:
                # Không gọi tool, giả lập stream lại từ nội dung đã lấy (vì ta đã lỡ request sync ở trên)
                content = message_obj.get("content", "")
                self._add_to_history(
                    session_id, {"role": "assistant", "content": content}
                )

                # Cắt chuỗi để giả lập stream nhanh
                chunk_size = 20
                for i in range(0, len(content), chunk_size):
                    chunk = content[i : i + chunk_size]
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
                    time.sleep(0.01)

        except Exception as e:
            raise ValueError(f"Không thể kết nối đến NVIDIA API. Chi tiết: {str(e)}")

    def _get_history(self, session_id: str) -> list:
        from db.connection import execute_query
        import json

        try:
            records = execute_query(
                "SELECT role, content, tool_calls, tool_call_id "
                "FROM chat_message WHERE session_id = %s ORDER BY created_at ASC",
                (session_id,),
            )
            if not records:
                return []

            history = []
            for r in records[-30:]:
                msg = {"role": r["role"]}
                if r.get("content"):
                    msg["content"] = r["content"]
                if r.get("tool_calls"):
                    try:
                        msg["tool_calls"] = json.loads(r["tool_calls"])
                    except (TypeError, ValueError, json.JSONDecodeError):
                        pass
                if r.get("tool_call_id"):
                    msg["tool_call_id"] = r["tool_call_id"]
                history.append(msg)
            return history
        except Exception:
            return []

    def _add_to_history(self, session_id: str, message: dict):
        from db.connection import execute_query, execute_update
        import json

        try:
            # Kiểm tra xem session đã tồn tại chưa
            exists = execute_query(
                "SELECT id FROM chat_session WHERE id = %s", (session_id,)
            )
            if not exists:
                execute_update(
                    "INSERT INTO chat_session (id, user_id, role, title) VALUES (%s, %s, %s, %s)",
                    (session_id, session_id, "user", "Trò chuyện"),
                )

            role = message.get("role", "assistant")
            content = message.get("content")
            tool_calls_str = (
                json.dumps(message.get("tool_calls"))
                if message.get("tool_calls")
                else None
            )
            tool_call_id = message.get("tool_call_id")

            execute_update(
                "INSERT INTO chat_message (session_id, role, content, tool_calls, tool_call_id) VALUES (%s, %s, %s, %s, %s)",
                (session_id, role, content, tool_calls_str, tool_call_id),
            )
        except Exception as e:
            print(f"[AIChatbot] Lỗi lưu lịch sử: {e}")
            pass


# ─── SINGLETON ───────────────────────────────────────────────────────────
_chatbot_instance = None


def get_chatbot() -> AIChatbot:
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = AIChatbot()
    return _chatbot_instance
