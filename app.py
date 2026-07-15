"""
Application Factory và Giao tiếp Socket.IO
Điểm vào (Entry point) khởi chạy toàn bộ Web Server
"""

import os
import eventlet
# Sử dụng eventlet cho WebSocket hiệu năng cao, nhưng KHÔNG patch thread để tránh deadlock với ChromaDB (native threads)
eventlet.monkey_patch(thread=False)

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
from flasgger import Swagger
from config import config_map, Config

# Global SocketIO object
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_name='default'):
    """Tạo instance Flask ứng với config pattern"""
    app = Flask(__name__)
    CORS(app) # Enable CORS for all routes
    
    # Cấu hình Swagger UI (Flasgger)
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "MTUFace API Documentation",
            "description": "Danh sách tất cả các API đang sử dụng trong hệ thống Kiosk, Mobile App và Web",
            "version": "1.0.0"
        }
    }
    Swagger(app, template=swagger_template)
    
    # Nạp config
    app.config.from_object(config_map[config_name])
    
    # Register blueprints
    from routes import (
        auth_bp, dashboard_bp, students_bp, classes_bp,
        attendance_bp, training_bp, camera_mgmt_bp, 
        export_bp, public_bp, api_mobile_bp,
        chatbot_bp, fraud_bp
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
    from routes.support import support_bp
    app.register_blueprint(support_bp, url_prefix='/support')
    
    # Init SocketIO
    socketio.init_app(app, async_mode='eventlet')
    
    # Khởi tạo Firebase Admin
    from services.fcm_service import init_firebase
    init_firebase()
    
    # Error handlers — Trang lỗi đẹp mắt
    from datetime import datetime
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/error.html',
            error_code=404,
            error_title="Trang Không Tồn Tại",
            error_message="Trang bạn tìm kiếm không tồn tại hoặc đã bị di chuyển. Kiểm tra lại đường dẫn URL.",
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/error.html',
            error_code=500,
            error_title="Lỗi Máy Chủ",
            error_message="Hệ thống gặp lỗi không mong muốn. Vui lòng thử lại sau hoặc liên hệ quản trị viên.",
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/error.html',
            error_code=403,
            error_title="Truy Cập Bị Từ Chối",
            error_message="Bạn không có quyền truy cập vào tài nguyên này. Vui lòng đăng nhập với tài khoản phù hợp.",
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), 403
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template('errors/error.html',
            error_code=405,
            error_title="Phương Thức Không Hỗ Trợ",
            error_message="Phương thức HTTP bạn sử dụng không được hỗ trợ cho trang này.",
            now=datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        ), 405
        
    # Khởi tạo các thư mục rỗng
    Config.init_dirs()

    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        """Expose uploaded image files."""
        return send_from_directory(Config.UPLOAD_FOLDER, filename)
    
    return app

# Khởi tạo the app
app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.route('/database/<path:filename>')
def serve_database_file(filename):
    return send_from_directory(Config.DATABASE_DIR, filename)

@app.route('/evidence/<path:filename>')
def serve_evidence_file(filename):
    return send_from_directory(Config.EVIDENCE_DIR, filename)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 MÁY CHỦ NHẬN DIỆN KHUÔN MẶT ĐANG KHỞI ĐỘNG...")
    print(f"👉 URL: http://localhost:5001")
    print(f"👉 Chế độ: {os.getenv('FLASK_ENV', 'development')}")
    print("="*50 + "\n")
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
    socketio.run(app, host='0.0.0.0', port=5001, debug=app.config['DEBUG'])
