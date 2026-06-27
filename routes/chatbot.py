"""
Chatbot Routes — API endpoints cho AI Chatbot MTUFace
Cung cấp giao diện chat và API tương tác với trợ lý AI
"""

import uuid
import re
import io
from flask import Blueprint, render_template, request, jsonify, session, Response
import json
import time

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')


@chatbot_bp.route('/')
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
    # Tạo session_id cho cuộc trò chuyện
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())

    from services.knowledge_builder import get_knowledge_builder
    from services.ai_chatbot import get_chatbot

    kb = get_knowledge_builder()
    chatbot = get_chatbot()

    return render_template('chatbot/chat.html',
        kb_status=kb.get_status(),
        suggested_questions=chatbot.get_suggested_questions(),
    )


@chatbot_bp.route('/ask', methods=['POST'])
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
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({"error": "Câu hỏi không được để trống"}), 400

    if len(question) > 2000:
        return jsonify({"error": "Câu hỏi quá dài (tối đa 2000 ký tự)"}), 400

    session_id = session.get('chat_session_id', 'default')

    # --- HỖ TRỢ APP MOBILE: Lấy MSSV từ token nếu có ---
    mssv = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            import jwt
            from config import Config
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            if payload.get('role') == 'student':
                mssv = payload.get('username')
                session_id = f"mobile_{mssv}" # Dùng mssv làm session cho mobile
        except Exception:
            pass

    from services.ai_chatbot import get_chatbot
    chatbot = get_chatbot()
    result = chatbot.chat(question, session_id, student_mssv=mssv)

    return jsonify(result)


@chatbot_bp.route('/clear', methods=['POST'])
def clear_chat():
    """
    API: Xóa lịch sử chat
    ---
    tags:
      - Chatbot AI API
    responses:
      200:
        description: Thành công
    """
    session_id = session.get('chat_session_id', 'default')

    from services.ai_chatbot import get_chatbot
    chatbot = get_chatbot()
    chatbot.clear_history(session_id)

    # Tạo session mới
    session['chat_session_id'] = str(uuid.uuid4())

    return jsonify({"success": True, "message": "Đã xóa lịch sử trò chuyện"})


@chatbot_bp.route('/build-knowledge', methods=['POST'])
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


@chatbot_bp.route('/knowledge-progress')
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
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@chatbot_bp.route('/knowledge-status')
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


@chatbot_bp.route('/tts', methods=['GET', 'POST'])
def text_to_speech():
    """
    API: Chuyển text thành giọng nói tiếng Việt (gTTS)
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        text = data.get('text', '').strip()
    else:
        text = request.args.get('text', '').strip()

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
            mimetype='audio/mpeg',
            headers={
                'Content-Type': 'audio/mpeg',
                'Cache-Control': 'no-cache',
            }
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
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.write_to_fp(buffer)
    buffer.seek(0)
    audio_data = buffer.read()

    print(f"[TTS] Generated {len(audio_data)} bytes of Vietnamese audio")
    return audio_data


def _clean_for_speech(text: str) -> str:
    """Remove markdown formatting for clean TTS output"""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)   # bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)        # italic
    text = re.sub(r'#{1,6}\s*', '', text)           # headers
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # links
    text = re.sub(r'```[\s\S]*?```', '', text)      # code blocks
    text = re.sub(r'`([^`]+)`', r'\1', text)        # inline code
    text = re.sub(r'^[\s]*[-\u2022*]\s*', '', text, flags=re.MULTILINE)  # bullets
    # Remove emojis
    text = re.sub(
        r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF'
        r'\U00002600-\U000026FF\U00002700-\U000027BF]', '', text
    )
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\n', '. ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()
