"""
Mobile Students, Classes, Schedule & Chatbot API routes.
"""
from flask import request, jsonify
from db.connection import execute_one, execute_query, execute_update
from . import api_mobile_bp
from .helpers import _require_mobile_auth, limiter


@api_mobile_bp.route('/classes', methods=['GET'])
def get_classes():
    """
    Lấy danh sách lớp học cho màn hình đăng ký
    """
    try:
        from services import class_service
        classes = class_service.get_all(active_only=True)
        res_data = [{"id": c["id"], "ma_lop": c["ma_lop"], "ten_lop": c["ten_lop"]} for c in classes]
        return jsonify({"success": True, "data": res_data}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/schedule', methods=['GET'])
def get_schedule():
    """
    Lấy lịch học của sinh viên
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    
    if payload.get('role') != 'student':
        return jsonify({"success": False, "message": "Chỉ sinh viên mới có lịch học"}), 403

    user_id = payload.get('sub')
    student = execute_one("SELECT lop_id FROM sinh_vien WHERE id = %s", (user_id,))
    
    if not student or not student['lop_id']:
        return jsonify({"success": True, "data": [], "message": "Sinh viên chưa được xếp lớp"}), 200
        
    sql = "SELECT * FROM lich_hoc WHERE lop_id = %s ORDER BY thu ASC, gio_bat_dau ASC"
    schedules = execute_query(sql, (student['lop_id'],))
    
    return jsonify({"success": True, "data": schedules}), 200


@api_mobile_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """
    Lấy danh sách thông báo của sinh viên
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        if payload.get('role') != 'student':
            return jsonify({"success": True, "data": []}), 200

        user_id = payload.get('sub')
        sql = "SELECT TOP 50 * FROM thong_bao WHERE sinh_vien_id = %s ORDER BY created_at DESC"
        results = execute_query(sql, (user_id,))
        
        for r in results:
            if hasattr(r['created_at'], 'strftime'):
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
def mark_notification_read(notif_id):
    """
    Đánh dấu thông báo đã đọc
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        execute_update("UPDATE thong_bao SET da_doc = 1 WHERE id = %s", (notif_id,))
        return jsonify({"success": True, "message": "Đã đọc"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    """
    Đánh dấu tất cả thông báo đã đọc
    """
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error: return auth_error
        
        user_id = payload.get('sub')
        execute_update("UPDATE thong_bao SET da_doc = 1 WHERE sinh_vien_id = %s", (user_id,))
        return jsonify({"success": True, "message": "Đã đọc tất cả"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ================================================================
# AI CHATBOT (Hỏi đáp AI trên Mobile)
# ================================================================

@api_mobile_bp.route('/chatbot/ask', methods=['POST'])
@limiter.limit("20 per minute")
def mobile_chatbot_ask():
    """
    Gửi câu hỏi cho AI Chatbot từ Mobile App
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()

    if not question:
        return jsonify({"success": False, "message": "Câu hỏi không được để trống"}), 400

    if len(question) > 2000:
        return jsonify({"success": False, "message": "Câu hỏi quá dài (tối đa 2000 ký tự)"}), 400

    user_id = payload.get('sub', 'unknown')
    session_id = f"mobile_{user_id}"

    try:
        from services.ai_chatbot import get_chatbot
        chatbot = get_chatbot()
        
        user_context = {
            'role': payload.get('role', 'student'),
            'username': payload.get('username'),
            'id': payload.get('sub')
        }
        
        result = chatbot.chat(question, session_id, user_context=user_context)

        return jsonify({
            "success": True,
            "data": {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "duration_ms": result.get("duration_ms", 0),
                "backend": result.get("backend", "unknown"),
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi AI Chatbot: {str(e)}"}), 500


@api_mobile_bp.route('/chatbot/suggestions', methods=['GET'])
def mobile_chatbot_suggestions():
    """
    Lấy danh sách câu hỏi gợi ý cho chatbot
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    try:
        from services.ai_chatbot import get_chatbot
        chatbot = get_chatbot()
        suggestions = chatbot.get_suggested_questions()
        return jsonify({"success": True, "data": suggestions}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route('/chatbot/clear', methods=['POST'])
def mobile_chatbot_clear():
    """
    Xóa lịch sử chat AI trên mobile
    """
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error

    user_id = payload.get('sub', 'unknown')
    session_id = f"mobile_{user_id}"

    try:
        from services.ai_chatbot import get_chatbot
        chatbot = get_chatbot()
        chatbot.clear_history(session_id)
        return jsonify({"success": True, "message": "Đã xóa lịch sử chat"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
