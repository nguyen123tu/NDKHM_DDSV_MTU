"""
Application Factory và Giao tiếp Socket.IO
Điểm vào (Entry point) khởi chạy toàn bộ Web Server
"""

import os
import eventlet

# Sử dụng eventlet cho WebSocket hiệu năng cao, nhưng KHÔNG patch thread để tránh deadlock với ChromaDB (native threads)
eventlet.monkey_patch(thread=False)

from flask import Flask, render_template, send_from_directory, request, session, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from flasgger import Swagger
import jwt
from config import config_map, Config
from core.csrf import init_csrf
from core.limiter import init_limiter

# Global SocketIO object (origins configured per-app in create_app)
socketio = SocketIO()


def create_app(config_name="default"):
    """Tạo instance Flask ứng với config pattern"""
    config_class = config_map.get(config_name, config_map["default"])
    if hasattr(config_class, "validate_config"):
        config_class.validate_config()

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Restrict CORS to ALLOWED_ORIGINS
    CORS(app, origins=app.config.get("ALLOWED_ORIGINS", ["*"]))

    # Kích hoạt bảo vệ CSRF
    init_csrf(app)

    # Kích hoạt Rate Limiter
    init_limiter(app)

    # Cấu hình Swagger UI (Flasgger)
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "MTUFace API Documentation",
            "description": "Danh sách tất cả các API đang sử dụng trong hệ thống Kiosk, Mobile App và Web",
            "version": "1.0.0",
        },
    }
    Swagger(app, template=swagger_template)

    # Nạp config đã được gọi ở trên
    # Register blueprints
    from routes import (
        auth_bp,
        dashboard_bp,
        students_bp,
        classes_bp,
        attendance_bp,
        training_bp,
        camera_mgmt_bp,
        export_bp,
        public_bp,
        api_mobile_bp,
        chatbot_bp,
        fraud_bp,
        users_bp,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(camera_mgmt_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(api_mobile_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(fraud_bp)
    app.register_blueprint(users_bp)
    from routes.support import support_bp

    app.register_blueprint(support_bp, url_prefix="/support")

    # Init SocketIO with allowed origins
    socketio.init_app(
        app,
        async_mode="eventlet",
        cors_allowed_origins=app.config.get("ALLOWED_ORIGINS", ["*"]),
    )

    # Khởi tạo Firebase Admin
    from services.fcm_service import init_firebase

    init_firebase()

    # Đăng ký centralized error handler & structured logging
    from core.error_handler import register_error_handlers

    register_error_handlers(app)

    # Khởi tạo các thư mục rỗng
    Config.init_dirs()

    def _is_authorized_file_access(filename, file_type):
        """Kiểm tra quyền truy cập file sinh trắc học và ảnh bằng chứng"""
        if session.get("admin_id") or session.get("giang_vien_id"):
            return True

        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        if not token:
            token = request.args.get("token")

        if token:
            try:
                payload = jwt.decode(
                    token,
                    app.config.get("JWT_SECRET_KEY", Config.SECRET_KEY),
                    algorithms=["HS256"],
                )
                role = payload.get("role")
                if role in ("admin", "teacher"):
                    return True

                # Student can only access their own files
                if role == "student":
                    user_id = payload.get("sub")
                    if not user_id:
                        return False

                    from db.connection import execute_one

                    if file_type == "database":
                        # Check if filename starts with student's mssv
                        sv = execute_one(
                            "SELECT mssv FROM sinh_vien WHERE id = %s", (user_id,)
                        )
                        if sv and filename.startswith(f"{sv['mssv']}"):
                            return True
                    elif file_type == "evidence":
                        # Check if evidence belongs to this student's leave request
                        # filename might be stored in minh_chung_url as '/evidence/filename'
                        check = execute_one(
                            "SELECT 1 FROM don_xin_phep WHERE sinh_vien_id = %s AND minh_chung_url LIKE %s",
                            (user_id, f"%{filename}%"),
                        )
                        if check:
                            return True
                    elif file_type == "uploads":
                        return True  # uploads might be public or less sensitive

                return False
            except Exception:
                return False

        # Fallback for web session
        if session.get("user_id"):
            user_id = session.get("user_id")
            from db.connection import execute_one

            if file_type == "database":
                sv = execute_one("SELECT mssv FROM sinh_vien WHERE id = %s", (user_id,))
                if sv and filename.startswith(f"{sv['mssv']}"):
                    return True
            elif file_type == "evidence":
                check = execute_one(
                    "SELECT 1 FROM don_xin_phep WHERE sinh_vien_id = %s AND minh_chung_url LIKE %s",
                    (user_id, f"%{filename}%"),
                )
                if check:
                    return True
            elif file_type == "uploads":
                return True

        return False

    @app.route("/uploads/<path:filename>")
    def serve_uploaded_file(filename):
        """Expose uploaded image files securely."""
        if not _is_authorized_file_access(filename, "uploads"):
            return (
                jsonify({"success": False, "message": "Unauthorized access to file"}),
                401,
            )
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

    @app.route("/database/<path:filename>")
    def serve_database_file(filename):
        if not _is_authorized_file_access(filename, "database"):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Unauthorized access to biometric file",
                    }
                ),
                401,
            )
        return send_from_directory(Config.DATABASE_DIR, filename)

    @app.route("/evidence/<path:filename>")
    def serve_evidence_file(filename):
        if not _is_authorized_file_access(filename, "evidence"):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Unauthorized access to evidence file",
                    }
                ),
                401,
            )
        return send_from_directory(Config.EVIDENCE_DIR, filename)

    return app


# Khởi tạo the app
app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🚀 MÁY CHỦ NHẬN DIỆN KHUÔN MẶT ĐANG KHỞI ĐỘNG...")
    print(f"👉 URL: http://localhost:5001")
    print(f"👉 Chế độ: {os.getenv('FLASK_ENV', 'development')}")
    print("=" * 50 + "\n")
    # Tải mô hình AI trong luồng nền (Background Thread)
    # Giúp server khởi động ngay lập tức mà vẫn giữ được trải nghiệm mượt mà khi người dùng điểm danh
    import threading

    def preload_models():
        print("\n[BACKGROUND] Đang tải AI Models vào RAM...")
        from core.matcher import get_matcher

        get_matcher()
        from core.engine import get_engine

        get_engine()
        print("[BACKGROUND] Tải AI Models hoàn tất! Hệ thống đã sẵn sàng 100%.\n")

    threading.Thread(target=preload_models, daemon=True).start()

    # Khởi động SocketIO app
    socketio.run(app, host="0.0.0.0", port=5001, debug=app.config["DEBUG"])
