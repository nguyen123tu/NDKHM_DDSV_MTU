"""
Cấu hình hệ thống điểm danh nhận diện khuôn mặt.
Đọc biến môi trường từ file .env
"""

import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()


class Config:
    """Cấu hình chung cho toàn bộ hệ thống"""

    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'mtu_super_secret_key_2026')

    # Database MySQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'face_attendance_db')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # Đường dẫn thư mục
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'database')

    # AI Model Paths
    EMBEDDINGS_PATH = os.path.join(MODELS_DIR, 'embeddings.pkl')
    EMBEDDINGS_YOLO_PATH = os.path.join(MODELS_DIR, 'embeddings_yolo_resnet.pkl')
    
    # AI Engine: 'insightface' hoặc 'yolo_resnet'
    AI_ENGINE = os.getenv('AI_ENGINE', 'insightface')

    # Ngưỡng nhận diện AI
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.45))
    MOTION_AREA_THRESHOLD = int(os.getenv('MOTION_THRESHOLD', 3000))
    ALERT_COOLDOWN_SEC = int(os.getenv('ALERT_COOLDOWN', 20))
    DB_LOG_COOLDOWN_SEC = int(os.getenv('DB_LOG_COOLDOWN', 28800))

    # Camera
    DET_SIZE = (640, 640)
    MAX_FPS = 15

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # Session
    SESSION_TYPE = 'filesystem'

    @classmethod
    def init_dirs(cls):
        """Tạo các thư mục cần thiết nếu chưa tồn tại"""
        for path in [cls.DATABASE_DIR, cls.MODELS_DIR]:
            if not os.path.exists(path):
                os.makedirs(path)


class DevelopmentConfig(Config):
    """Cấu hình dành cho môi trường phát triển"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Cấu hình dành cho môi trường sản phẩm"""
    DEBUG = False
    FLASK_ENV = 'production'


# Mapping tên cấu hình
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
