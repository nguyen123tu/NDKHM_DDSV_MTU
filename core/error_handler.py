"""
Centralized Error Handler and Stack Trace Logging for MTUFace.
Provides unified exception handling for both web templates and API (JSON) requests.
"""
import logging
import traceback
from datetime import datetime
from flask import request, jsonify, render_template, current_app
from werkzeug.exceptions import HTTPException


# Configure root logger for structured logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] [%(pathname)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("MTUFace.Error")


def _is_api_request():
    """
    Xác định xem request có yêu cầu phản hồi dạng JSON hay không.
    """
    if request.path.startswith('/api/') or request.path.startswith('/chatbot/'):
        return True
    if request.is_json:
        return True
    accept = request.headers.get('Accept', '')
    if 'application/json' in accept and 'text/html' not in accept:
        return True
    return False


def register_error_handlers(app):
    """
    Đăng ký bộ xử lý lỗi tập trung cho ứng dụng Flask.
    """

    @app.errorhandler(400)
    def handle_bad_request(e):
        code = 400
        message = getattr(e, 'description', 'Yêu cầu không hợp lệ hoặc thiếu dữ liệu cần thiết.')
        logger.warning(f"400 Bad Request: {request.method} {request.path} - {message}")
        if _is_api_request():
            return jsonify({"success": False, "error": code, "message": message}), code
        return render_template('errors/error.html',
            error_code=code,
            error_title="Yêu Cầu Không Hợp Lệ",
            error_message=message,
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), code

    @app.errorhandler(403)
    def handle_forbidden(e):
        code = 403
        message = getattr(e, 'description', 'Bạn không có quyền truy cập vào tài nguyên này.')
        logger.warning(f"403 Forbidden: {request.method} {request.path} - {message}")
        if _is_api_request():
            return jsonify({"success": False, "error": code, "message": message}), code
        return render_template('errors/error.html',
            error_code=code,
            error_title="Truy Cập Bị Từ Chối",
            error_message=message,
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), code

    @app.errorhandler(404)
    def handle_not_found(e):
        code = 404
        message = getattr(e, 'description', 'Tài nguyên hoặc trang bạn tìm kiếm không tồn tại.')
        logger.warning(f"404 Not Found: {request.method} {request.path}")
        if _is_api_request():
            return jsonify({"success": False, "error": code, "message": message}), code
        return render_template('errors/error.html',
            error_code=code,
            error_title="Trang Không Tồn Tại",
            error_message="Trang bạn tìm kiếm không tồn tại hoặc đã bị di chuyển. Kiểm tra lại đường dẫn URL.",
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), code

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        code = 405
        message = getattr(e, 'description', f'Phương thức {request.method} không được hỗ trợ cho đường dẫn này.')
        logger.warning(f"405 Method Not Allowed: {request.method} {request.path}")
        if _is_api_request():
            return jsonify({"success": False, "error": code, "message": message}), code
        return render_template('errors/error.html',
            error_code=code,
            error_title="Phương Thức Không Hỗ Trợ",
            error_message=message,
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), code

    @app.errorhandler(429)
    def handle_rate_limit(e):
        code = 429
        message = getattr(e, 'description', 'Bạn đang gửi quá nhiều yêu cầu. Vui lòng thử lại sau giây lát.')
        logger.warning(f"429 Too Many Requests: {request.method} {request.path} - {request.remote_addr}")
        if _is_api_request():
            return jsonify({"success": False, "error": code, "message": message}), code
        return render_template('errors/error.html',
            error_code=code,
            error_title="Quá Nhiều Yêu Cầu",
            error_message=message,
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), code

    @app.errorhandler(500)
    def handle_internal_error(e):
        code = 500
        logger.error(f"500 Internal Server Error: {request.method} {request.path}", exc_info=True)
        message = "Hệ thống gặp lỗi máy chủ nội bộ. Vui lòng thử lại sau hoặc liên hệ quản trị viên."
        if getattr(current_app, 'debug', False):
            message = str(e)
        if _is_api_request():
            return jsonify({"success": False, "error": code, "message": message}), code
        return render_template('errors/error.html',
            error_code=code,
            error_title="Lỗi Máy Chủ",
            error_message=message,
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), code

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        # Nếu là HTTPException (4xx, 5xx), xử lý theo mã HTTP
        if isinstance(e, HTTPException):
            code = e.code or 500
            message = e.description
            logger.warning(f"HTTPException {code}: {request.method} {request.path} - {message}")
            if _is_api_request():
                return jsonify({"success": False, "error": code, "message": message}), code
            return render_template('errors/error.html',
                error_code=code,
                error_title=f"Lỗi {code}",
                error_message=message,
                now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
            ), code

        # Unhandled Python Exception (e.g. ValueError, KeyError, DB error, etc.)
        code = 500
        logger.exception(f"Unhandled Exception on {request.method} {request.path}: {str(e)}")
        message = "Hệ thống gặp lỗi không mong muốn. Vui lòng thử lại sau."
        if getattr(current_app, 'debug', False):
            message = f"Unhandled Exception: {str(e)}"
        if _is_api_request():
            return jsonify({"success": False, "error": code, "message": message}), code
        return render_template('errors/error.html',
            error_code=code,
            error_title="Lỗi Máy Chủ",
            error_message=message,
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), code
