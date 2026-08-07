"""
Chatbot Routes — API endpoints cho AI Chatbot MTUFace
Cung cấp giao diện chat và API tương tác với trợ lý AI
"""

import re
import io
from flask import (
    Blueprint,
    Response,
    jsonify,
    render_template,
    request,
    send_from_directory,
    session,
)
import json
import time
from utils.decorators import login_required, admin_required
from core.limiter import limiter

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


def _web_conversation_id(data=None):
    """Tạo khóa DB riêng cho từng người dùng và từng cuộc hội thoại."""
    data = data or {}
    conversation_id = str(
        data.get("conversation_id") or request.args.get("conversation_id") or "main"
    )
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", conversation_id):
        raise ValueError("conversation_id không hợp lệ")
    return f"web_{session['admin_id']}_{conversation_id}"


@chatbot_bp.route("/")
@login_required
def chat_page():
    """
    Trang chat AI
    ---
    tags:
      - Chatbot AI API
    responses:
      200:
        description: Thành công
    """
    from services.knowledge_builder import get_knowledge_builder
    from services.ai_chatbot import get_chatbot

    kb = get_knowledge_builder()
    chatbot = get_chatbot()

    return render_template(
        "chatbot/chat.html",
        kb_status=kb.get_status(),
        suggested_questions=chatbot.get_suggested_questions(),
    )


@chatbot_bp.route("/ask", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def ask():
    """
    API: Gửi câu hỏi cho AI
    ---
    tags:
      - Chatbot AI API
    responses:
      200:
        description: Thành công
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Câu hỏi không được để trống"}), 400

    if len(question) > 2000:
        return jsonify({"error": "Câu hỏi quá dài (tối đa 2000 ký tự)"}), 400

    try:
        session_id = _web_conversation_id(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # --- HỖ TRỢ APP MOBILE & WEB: Lấy User Context ---
    user_context = None

    # 1. Từ Web Session
    if "admin_username" in session:
        user_context = {
            "role": session.get("admin_role", "admin"),
            "username": session.get("admin_username"),
            "id": session.get("admin_id"),
            "name": session.get("admin_name"),
        }

    from services.ai_chatbot import get_chatbot

    chatbot = get_chatbot()
    result = chatbot.chat(question, session_id, user_context=user_context)

    return jsonify(result)


@chatbot_bp.route("/ask_stream", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def ask_stream():
    """
    API: Gửi câu hỏi cho AI (Streaming SSE)
    """
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Câu hỏi không được để trống"}), 400

    if len(question) > 2000:
        return jsonify({"error": "Câu hỏi quá dài (tối đa 2000 ký tự)"}), 400

    try:
        session_id = _web_conversation_id(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # --- HỖ TRỢ APP MOBILE & WEB: Lấy User Context ---
    user_context = None

    # 1. Từ Web Session
    if "admin_username" in session:
        user_context = {
            "role": session.get("admin_role", "admin"),
            "username": session.get("admin_username"),
            "id": session.get("admin_id"),
            "name": session.get("admin_name"),
        }

    from services.ai_chatbot import get_chatbot

    chatbot = get_chatbot()

    return Response(
        chatbot.chat_stream(question, session_id, user_context=user_context),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@chatbot_bp.route("/suggestions", methods=["GET"])
@login_required
def mobile_chatbot_suggestions():
    # Helper for mobile app
    from services.ai_chatbot import get_chatbot

    chatbot = get_chatbot()
    suggestions = chatbot.get_suggested_questions()
    return jsonify({"success": True, "data": suggestions}), 200


@chatbot_bp.route("/history", methods=["GET"])
@login_required
def get_chat_history():
    """
    API: Lấy lịch sử chat
    """
    try:
        session_id = _web_conversation_id()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    from services.ai_chatbot import get_chatbot
    chatbot = get_chatbot()
    history = chatbot._get_history(session_id)
    return jsonify({"success": True, "history": history})

@chatbot_bp.route("/clear", methods=["POST"])
@login_required
def clear_chat():
    """
    API: Xóa lịch sử chat
    """
    data = request.get_json(silent=True) or {}
    try:
        session_id = _web_conversation_id(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    from services.ai_chatbot import get_chatbot
    chatbot = get_chatbot()
    chatbot.clear_history(session_id)

    return jsonify({"success": True, "message": "Đã xóa lịch sử trò chuyện"})


@chatbot_bp.route("/build-knowledge", methods=["POST"])
@login_required
@admin_required
def build_knowledge():
    """
    API: Xây dựng/rebuild kho tri thức
    ---
    tags:
      - Chatbot AI API
    responses:
      200:
        description: Thành công
    """
    from services.knowledge_builder import get_knowledge_builder

    kb = get_knowledge_builder()
    result = kb.build()
    return jsonify(result)


@chatbot_bp.route("/knowledge-progress")
@login_required
@admin_required
def knowledge_progress():
    """
    SSE: Stream tiến độ xây dựng kho tri thức
    ---
    tags:
      - Chatbot AI API
    responses:
      200:
        description: Thành công
    """
    from services.knowledge_builder import get_knowledge_builder

    kb = get_knowledge_builder()

    def stream():
        while True:
            progress = kb.get_progress()
            yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"

            if progress["status"] in ("done", "error", "idle"):
                break
            time.sleep(0.5)

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@chatbot_bp.route("/download-export/<path:filename>")
@login_required
def download_export(filename):
    """
    Tải file báo cáo do AI sinh ra
    """
    import os
    from flask import send_from_directory

    exports_dir = os.path.join(os.path.dirname(__file__), "..", "static", "exports")
    return send_from_directory(exports_dir, filename, as_attachment=True)


@chatbot_bp.route("/knowledge-status")
@login_required
@admin_required
def knowledge_status():
    """
    API: Trạng thái kho tri thức
    ---
    tags:
      - Chatbot AI API
    responses:
      200:
        description: Thành công
    """
    from services.knowledge_builder import get_knowledge_builder

    kb = get_knowledge_builder()
    return jsonify(kb.get_status())


@chatbot_bp.route("/tts", methods=["GET", "POST"])
@limiter.limit("30 per minute")
def text_to_speech():
    """
    API: Chuyển text thành giọng nói tiếng Việt (gTTS)
    """
    if request.method == "POST":
        data = request.get_json() or {}
        text = data.get("text", "").strip()
    else:
        text = request.args.get("text", "").strip()

    if not text:
        return jsonify({"error": "Text không được để trống"}), 400

    if len(text) > 5000:
        return jsonify({"error": "Text quá dài (tối đa 5000 ký tự)"}), 400

    # Clean markdown for speech
    clean_text = _clean_for_speech(text)
    if not clean_text:
        return jsonify({"error": "Text sau khi xử lý trống"}), 400

    try:
        audio_data = _generate_tts(clean_text)
        return Response(
            audio_data,
            mimetype="audio/mpeg",
            headers={
                "Content-Type": "audio/mpeg",
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": f"TTS error: {str(e)}"}), 500


def _generate_tts(text: str) -> bytes:
    """
    Generate TTS audio using Google Text-to-Speech (gTTS).
    - Miễn phí, không cần API key
    - Hỗ trợ tiếng Việt tốt
    - Sync, tương thích hoàn toàn với eventlet
    """
    from gtts import gTTS

    buffer = io.BytesIO()
    tts = gTTS(text=text, lang="vi", slow=False)
    tts.write_to_fp(buffer)
    buffer.seek(0)
    audio_data = buffer.read()

    print(f"[TTS] Generated {len(audio_data)} bytes of Vietnamese audio")
    return audio_data


def _clean_for_speech(text: str) -> str:
    """Remove markdown formatting for clean TTS output"""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # italic
    text = re.sub(r"#{1,6}\s*", "", text)  # headers
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links
    text = re.sub(r"```[\s\S]*?```", "", text)  # code blocks
    text = re.sub(r"`([^`]+)`", r"\1", text)  # inline code
    text = re.sub(r"^[\s]*[-\u2022*]\s*", "", text, flags=re.MULTILINE)  # bullets
    # Remove emojis
    text = re.sub(
        r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF"
        r"\U00002600-\U000026FF\U00002700-\U000027BF]",
        "",
        text,
    )
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\n", ". ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()
