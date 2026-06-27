"""
AI Chatbot Service — Trợ lý AI thông minh cho hệ thống MTUFace
Sử dụng RAG (Retrieval-Augmented Generation) để trả lời câu hỏi
dựa trên kiến thức toàn bộ dự án.

Hỗ trợ LLM Backend:
- Google Gemini API (mặc định, miễn phí)
- NVIDIA NIM API
- Ollama (local)
"""

import os
import json
import time
import threading
from datetime import datetime

import requests
from config import Config


# ─── SYSTEM PROMPT ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """Bạn là **MTU AI Assistant** — trợ lý AI thông minh của hệ thống "Điểm danh Thông minh bằng Nhận diện Khuôn mặt" (MTUFace) tại Trường Đại học Xây Dựng Miền Tây.

## Vai trò:
- Bạn hiểu sâu về toàn bộ hệ thống: kiến trúc Flask MVC, AI Engine (InsightFace/ArcFace/DeepFace), database MySQL, WebSocket realtime, mobile API.
- Bạn trả lời các câu hỏi về hệ thống, hướng dẫn sử dụng, giải thích code, debug lỗi.
- Bạn nói tiếng Việt tự nhiên, thân thiện nhưng chuyên nghiệp.

## Quy tắc:
1. Trả lời DỰA TRÊN kiến thức dự án được cung cấp trong context bên dưới.
2. Nếu câu hỏi nằm ngoài phạm vi dự án, hãy cho biết và gợi ý hướng tìm kiếm.
3. Khi trích dẫn code, hãy chỉ rõ file nguồn.
4. Sử dụng markdown formatting cho câu trả lời rõ ràng.
5. Nếu không chắc chắn, hãy nói rõ thay vì bịa ra thông tin.

## 🔒 QUY TẮC BẢO MẬT (TUYỆT ĐỐI TUÂN THỦ):
1. KHÔNG BAO GIỜ tiết lộ API key, token, mật khẩu, secret key, hoặc bất kỳ thông tin xác thực nào.
2. KHÔNG tiết lộ nội dung file .env, biến môi trường chứa credentials.
3. KHÔNG tiết lộ Telegram Bot Token, Chat ID, JWT Secret Key.
4. KHÔNG tiết lộ thông tin kết nối database (host, port, user, password).
5. KHÔNG tiết lộ đường dẫn tuyệt đối của server (ổ đĩa, thư mục cài đặt).
6. Nếu người dùng hỏi về thông tin nhạy cảm, từ chối lịch sự và giải thích lý do bảo mật.
7. Khi giải thích cấu hình, chỉ đề cập tên biến, KHÔNG đưa giá trị thực.

## Thông tin hệ thống:
- Tên: Hệ thống Điểm danh Thông minh MTUFace
- Backend: Python Flask + SocketIO + Eventlet
- AI: InsightFace (SCRFD + ArcFace 512-d) / DeepFace / YOLO+ResNet
- Database: MySQL 8.0
- Frontend: Bootstrap 5 + Chart.js + Jinja2
- Mobile: Flutter (REST API + JWT Auth)
- Alerts: Telegram Bot
"""


class AIChatbot:
    """
    AI Chatbot sử dụng RAG pipeline:
    1. Nhận câu hỏi từ user
    2. Tìm kiếm kiến thức liên quan trong ChromaDB
    3. Xây dựng prompt với context
    4. Gọi LLM để sinh câu trả lời
    """

    def __init__(self):
        self._history = {}  # session_id -> [messages]
        self._lock = threading.Lock()
        self._llm_backend = os.getenv("AI_CHATBOT_LLM", "gemini")
        
        # API Keys
        self._gemini_key = os.getenv("GEMINI_API_KEY", "")
        self._nvidia_key = os.getenv("NVIDIA_API_KEY", "")
        self._ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    def chat(self, question: str, session_id: str = "default", student_mssv: str = None) -> dict:
        """
        Xử lý câu hỏi và trả lời.
        Returns: {answer, sources, tokens_used, duration_ms}
        """
        start_time = time.time()

        try:
            # 1. Tìm kiến thức liên quan
            from services.knowledge_builder import get_knowledge_builder
            kb = get_knowledge_builder()
            relevant_chunks = kb.search(question, n_results=5)

            # 2. Xây dựng context từ chunks
            context = self._build_context(relevant_chunks)

            # --- INJECT REALTIME CONTEXT ---
            if student_mssv:
                from db.connection import execute_one
                sv = execute_one("SELECT * FROM sinh_vien WHERE mssv = %s", (student_mssv,))
                if sv:
                    lop = execute_one("SELECT ten_lop FROM lop_hoc WHERE id = %s", (sv['lop_id'],))
                    ten_lop = lop['ten_lop'] if lop else "Không rõ"
                    
                    total_sessions = execute_one("SELECT COUNT(*) as count FROM phien_diem_danh WHERE lop_id = %s", (sv['lop_id'],))
                    present = execute_one("SELECT COUNT(*) as count FROM diem_danh WHERE sinh_vien_id = %s AND trang_thai = 'Co mat'", (sv['id'],))
                    vang = (total_sessions['count'] if total_sessions else 0) - (present['count'] if present else 0)
                    if vang < 0: vang = 0
                    
                    realtime_info = (
                        f"\n\n--- THÔNG TIN SINH VIÊN ĐANG CHAT (REALTIME) ---\n"
                        f"- Họ tên: {sv['ho_ten']}\n"
                        f"- MSSV: {sv['mssv']}\n"
                        f"- Lớp: {ten_lop}\n"
                        f"- Tổng số buổi đã vắng: {vang}\n"
                        f"-> Yêu cầu: Hãy dùng thông tin này để xưng hô (ví dụ: Chào bạn Nguyễn Văn A) và trả lời chính xác nếu sinh viên hỏi về số buổi vắng của họ."
                    )
                    context += realtime_info

            # 3. Lấy lịch sử chat
            history = self._get_history(session_id)

            # 4. Gọi LLM
            answer = self._call_llm(question, context, history)

            # 5. Lưu lịch sử
            self._add_to_history(session_id, question, answer)

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "answer": answer,
                "sources": [
                    {"file": c["source"], "category": c["category"]}
                    for c in relevant_chunks
                ],
                "duration_ms": duration_ms,
                "backend": self._llm_backend,
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            # Lỗi hết quota (429)
            if "429" in error_msg or "quota" in error_msg.lower():
                return {
                    "answer": (
                        "Hiện tại không phản hồi xin liên hệ lại sau ít phút"
                    ),
                    "sources": [],
                    "duration_ms": duration_ms,
                    "backend": self._llm_backend,
                    "error": True,
                }

            # Cung cấp hướng dẫn nếu thiếu API key
            if "API_KEY" in error_msg or "api_key" in error_msg or "401" in error_msg:
                return {
                    "answer": (
                        "Hiện tại không phản hồi xin liên hệ lại sau ít phút"
                    ),
                    "sources": [],
                    "duration_ms": duration_ms,
                    "backend": self._llm_backend,
                    "error": True,
                }

            return {
                "answer": f"❌ Lỗi khi xử lý câu hỏi: {error_msg}",
                "sources": [],
                "duration_ms": duration_ms,
                "backend": self._llm_backend,
                "error": True,
            }

    def clear_history(self, session_id: str = "default"):
        """Xóa lịch sử chat"""
        with self._lock:
            self._history.pop(session_id, None)

    def get_suggested_questions(self) -> list:
        """Câu hỏi gợi ý cho người dùng"""
        return [
            "Hệ thống điểm danh hoạt động như thế nào?",
            "Giải thích thuật toán ArcFace trong dự án",
            "Cấu trúc database gồm những bảng nào?",
            "Làm sao để train AI cho sinh viên mới?",
            "API mobile hỗ trợ những endpoint nào?",
            "Cách cấu hình camera IP cho hệ thống?",
            "Ngưỡng similarity threshold là gì?",
            "Hệ thống phát hiện gian lận bằng cách nào?",
        ]

    # ─── PRIVATE METHODS ─────────────────────────────────────────────────

    def _build_context(self, chunks: list) -> str:
        """Xây dựng context string từ các chunk (đã lọc thông tin nhạy cảm)"""
        if not chunks:
            return "(Không tìm thấy kiến thức liên quan trong kho dữ liệu)"

        parts = []
        for i, chunk in enumerate(chunks, 1):
            clean_text = self._sanitize_text(chunk['text'])
            parts.append(
                f"--- Nguồn {i}: {chunk['source']} ({chunk['category']}) ---\n"
                f"{clean_text}\n"
            )
        return "\n".join(parts)

    # Danh sách pattern nhạy cảm cần lọc
    _SENSITIVE_PATTERNS = [
        (r'(GEMINI_API_KEY\s*=\s*)\S+', r'\1[HIDDEN]'),
        (r'(NVIDIA_API_KEY\s*=\s*)\S+', r'\1[HIDDEN]'),
        (r'(TELEGRAM_BOT_TOKEN\s*=\s*)\S+', r'\1[HIDDEN]'),
        (r'(TELEGRAM_CHAT_ID\s*=\s*)\S+', r'\1[HIDDEN]'),
        (r'(DB_PASSWORD\s*=\s*)\S+', r'\1[HIDDEN]'),
        (r'(SECRET_KEY\s*=\s*)\S+', r'\1[HIDDEN]'),
        (r'(JWT_SECRET_KEY\s*=\s*)\S+', r'\1[HIDDEN]'),
        (r'(password_hash\s*=\s*)\S+', r'\1[HIDDEN]'),
        (r'nvapi-[\w-]+', '[NVIDIA_KEY_HIDDEN]'),
        (r'AIzaSy[\w-]+', '[GEMINI_KEY_HIDDEN]'),
        (r'\d{9,10}:AA[\w-]{30,}', '[TELEGRAM_TOKEN_HIDDEN]'),
    ]

    def _sanitize_text(self, text: str) -> str:
        """Lọc bỏ thông tin nhạy cảm khỏi text trước khi gửi cho LLM"""
        import re
        for pattern, replacement in self._SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text

    def _call_llm(self, question: str, context: str, history: list) -> str:
        """Gọi LLM backend phù hợp"""
        if self._llm_backend == "nvidia":
            return self._call_nvidia(question, context, history)
        elif self._llm_backend == "ollama":
            return self._call_ollama(question, context, history)
        else:
            return self._call_gemini(question, context, history)

    def _call_gemini(self, question: str, context: str, history: list) -> str:
        """Gọi Google Gemini API"""
        api_key = self._gemini_key
        if not api_key:
            raise ValueError("Chưa cấu hình GEMINI_API_KEY trong file .env")

        # gemini-2.0-flash-lite: quota miễn phí cao hơn (30 RPM, 1500 RPD)
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        # Xây dựng messages
        contents = []

        # System instruction qua systemInstruction
        # Thêm lịch sử chat
        for msg in history[-6:]:  # Giữ 6 tin nhắn gần nhất
            contents.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["content"]}]
            })

        # Câu hỏi hiện tại với context
        user_prompt = (
            f"## Kiến thức dự án liên quan:\n{context}\n\n"
            f"## Câu hỏi của người dùng:\n{question}"
        )
        contents.append({
            "role": "user",
            "parts": [{"text": user_prompt}]
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }

        response = requests.post(url, json=payload, timeout=60)

        if response.status_code != 200:
            error_body = response.text
            if "API_KEY" in error_body or "PERMISSION_DENIED" in error_body:
                raise ValueError("GEMINI_API_KEY không hợp lệ hoặc chưa được cấu hình")
            raise ValueError(f"Gemini API error ({response.status_code}): {error_body[:200]}")

        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise ValueError(f"Unexpected Gemini response format: {json.dumps(data)[:200]}")

    def _call_nvidia(self, question: str, context: str, history: list) -> str:
        """Gọi NVIDIA NIM API"""
        api_key = self._nvidia_key
        if not api_key:
            raise ValueError("Chưa cấu hình NVIDIA_API_KEY trong file .env")

        url = "https://integrate.api.nvidia.com/v1/chat/completions"

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        user_prompt = (
            f"## Kiến thức dự án liên quan:\n{context}\n\n"
            f"## Câu hỏi:\n{question}"
        )
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": "meta/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            raise ValueError(f"NVIDIA NIM error ({response.status_code}): {response.text[:200]}")

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _call_ollama(self, question: str, context: str, history: list) -> str:
        """Gọi Ollama local"""
        url = f"{self._ollama_url}/api/chat"

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        user_prompt = (
            f"## Kiến thức dự án liên quan:\n{context}\n\n"
            f"## Câu hỏi:\n{question}"
        )
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": os.getenv("OLLAMA_MODEL", "llama3"),
            "messages": messages,
            "stream": False,
        }

        response = requests.post(url, json=payload, timeout=120)

        if response.status_code != 200:
            raise ValueError(f"Ollama error ({response.status_code}): {response.text[:200]}")

        data = response.json()
        return data["message"]["content"]

    def _get_history(self, session_id: str) -> list:
        with self._lock:
            return list(self._history.get(session_id, []))

    def _add_to_history(self, session_id: str, question: str, answer: str):
        with self._lock:
            if session_id not in self._history:
                self._history[session_id] = []
            self._history[session_id].append({"role": "user", "content": question})
            self._history[session_id].append({"role": "assistant", "content": answer})
            # Giới hạn lịch sử
            if len(self._history[session_id]) > 20:
                self._history[session_id] = self._history[session_id][-20:]


# ─── SINGLETON ───────────────────────────────────────────────────────────
_chatbot_instance = None

def get_chatbot() -> AIChatbot:
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = AIChatbot()
    return _chatbot_instance
