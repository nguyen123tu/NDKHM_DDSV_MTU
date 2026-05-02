"""
Chatbot Routes — API endpoints cho AI Chatbot MTUFace
Cung cấp giao diện chat và API tương tác với trợ lý AI
"""

import uuid
from flask import Blueprint, render_template, request, jsonify, session, Response
import json
import time

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')


@chatbot_bp.route('/')
def chat_page():
    """Trang chat AI"""
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
    """API: Gửi câu hỏi cho AI"""
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({"error": "Câu hỏi không được để trống"}), 400

    if len(question) > 2000:
        return jsonify({"error": "Câu hỏi quá dài (tối đa 2000 ký tự)"}), 400

    session_id = session.get('chat_session_id', 'default')

    from services.ai_chatbot import get_chatbot
    chatbot = get_chatbot()
    result = chatbot.chat(question, session_id)

    return jsonify(result)


@chatbot_bp.route('/clear', methods=['POST'])
def clear_chat():
    """API: Xóa lịch sử chat"""
    session_id = session.get('chat_session_id', 'default')

    from services.ai_chatbot import get_chatbot
    chatbot = get_chatbot()
    chatbot.clear_history(session_id)

    # Tạo session mới
    session['chat_session_id'] = str(uuid.uuid4())

    return jsonify({"success": True, "message": "Đã xóa lịch sử trò chuyện"})


@chatbot_bp.route('/build-knowledge', methods=['POST'])
def build_knowledge():
    """API: Xây dựng/rebuild kho tri thức"""
    from services.knowledge_builder import get_knowledge_builder
    kb = get_knowledge_builder()
    result = kb.build()
    return jsonify(result)


@chatbot_bp.route('/knowledge-progress')
def knowledge_progress():
    """SSE: Stream tiến độ xây dựng kho tri thức"""
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
    """API: Trạng thái kho tri thức"""
    from services.knowledge_builder import get_knowledge_builder
    kb = get_knowledge_builder()
    return jsonify(kb.get_status())
