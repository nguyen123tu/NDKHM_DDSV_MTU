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
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "")

    # CORS & WebSocket Allowed Origins
    ALLOWED_ORIGINS = [
        o.strip()
        for o in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:5001,http://127.0.0.1:5001"
        ).split(",")
        if o.strip()
    ]

    # Database Microsoft SQL Server
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 1433))
    DB_NAME = os.getenv("DB_NAME", "face_attendance_db")
    DB_USER = os.getenv("DB_USER", "sa")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", 20))
    DB_LOGIN_TIMEOUT_SEC = int(os.getenv("DB_LOGIN_TIMEOUT_SEC", 5))
    DB_QUERY_TIMEOUT_SEC = int(os.getenv("DB_QUERY_TIMEOUT_SEC", 15))
    DB_POOL_BLOCKING = os.getenv("DB_POOL_BLOCKING", "false").lower() == "true"

    # Đường dẫn thư mục
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    MODELS_DIR = os.path.join(BASE_DIR, "models")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "database")

    # AI Model Paths
    EMBEDDINGS_PATH = os.path.join(MODELS_DIR, "embeddings.npz")
    EMBEDDINGS_YOLO_PATH = os.path.join(MODELS_DIR, "embeddings_yolo_resnet.npz")
    EMBEDDINGS_DEEPFACE_PATH = os.path.join(MODELS_DIR, "embeddings_deepface.npz")

    # AI Engine: 'insightface', 'yolo_resnet', hoặc 'deepface'
    AI_ENGINE = os.getenv("AI_ENGINE", "insightface")

    # ─── DeepFace Engine Config ──────────────────────────────────────────
    # Chỉ áp dụng khi AI_ENGINE = 'deepface'
    # Model nhận diện: VGG-Face, Facenet, Facenet512, ArcFace, SFace,
    #                  GhostFaceNet, Dlib, DeepID, OpenFace, Buffalo_L
    DEEPFACE_MODEL = os.getenv("DEEPFACE_MODEL", "ArcFace")

    # Detector backend: opencv, retinaface, mtcnn, ssd, dlib, mediapipe,
    #                   yolov8n, yolov11n, centerface, yunet
    DEEPFACE_DETECTOR = os.getenv("DEEPFACE_DETECTOR", "retinaface")

    # Anti-spoofing: Chống giả mạo khuôn mặt (ảnh in, video, mặt nạ)
    DEEPFACE_ANTI_SPOOFING = (
        os.getenv("DEEPFACE_ANTI_SPOOFING", "false").lower() == "true"
    )
    ANTI_SPOOF_FAIL_OPEN = os.getenv("ANTI_SPOOF_FAIL_OPEN", "false").lower() == "true"

    # Face Analysis: Phân tích thuộc tính khuôn mặt khi điểm danh
    # Options: age, gender, emotion, race (phân tách bằng dấu phẩy)
    DEEPFACE_ANALYSIS_ACTIONS = os.getenv("DEEPFACE_ANALYSIS_ACTIONS", "")
    # ────────────────────────────────────────────────────────────────────

    # ─── AI Chatbot Config ───────────────────────────────────────────────
    # LLM Backend: 'gemini' (mặc định, miễn phí), 'nvidia', 'ollama'
    AI_CHATBOT_LLM = os.getenv("AI_CHATBOT_LLM", "gemini")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    # ────────────────────────────────────────────────────────────────────

    # Ngưỡng nhận diện AI
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.45))
    MOTION_AREA_THRESHOLD = int(os.getenv("MOTION_THRESHOLD", 3000))
    ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN", 20))
    DB_LOG_COOLDOWN_SEC = int(os.getenv("DB_LOG_COOLDOWN", 28800))

    # Camera
    DET_SIZE = (640, 640)
    MAX_FPS = max(1, int(os.getenv("MAX_FPS", 12)))
    AI_FRAME_SKIP = max(1, int(os.getenv("AI_FRAME_SKIP", 2)))
    WORKER_STOP_TIMEOUT_SEC = max(0.1, float(os.getenv("WORKER_STOP_TIMEOUT_SEC", 3)))
    CAMERA_RECONNECT_MAX_SEC = max(1.0, float(os.getenv("CAMERA_RECONNECT_MAX_SEC", 10)))

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # Session
    SESSION_TYPE = "filesystem"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV", "development") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Mobile API auth (JWT)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", 24))

    # Evidence image storage (MVP: local folder)
    EVIDENCE_DIR = os.path.join(BASE_DIR, "database", "evidence")
    MOBILE_ALLOWED_CHECKIN_EARLY_MIN = int(
        os.getenv("MOBILE_ALLOWED_CHECKIN_EARLY_MIN", 15)
    )
    MOBILE_ALLOWED_CHECKIN_LATE_MIN = int(
        os.getenv("MOBILE_ALLOWED_CHECKIN_LATE_MIN", 30)
    )
    LATE_GRACE_PERIOD_MIN = int(os.getenv("LATE_GRACE_PERIOD_MIN", 15))

    # Attendance score weights
    WEIGHT_PRESENT = float(os.getenv("WEIGHT_PRESENT", 1.0))
    WEIGHT_LATE = float(os.getenv("WEIGHT_LATE", 0.75))
    WEIGHT_EXCUSED = float(os.getenv("WEIGHT_EXCUSED", 1.0))
    WEIGHT_UNEXCUSED = float(os.getenv("WEIGHT_UNEXCUSED", 0.0))
    WEIGHT_EARLY_LEAVE = float(os.getenv("WEIGHT_EARLY_LEAVE", 0.5))

    @classmethod
    def init_dirs(cls):
        """Tạo các thư mục cần thiết nếu chưa tồn tại"""
        for path in [cls.DATABASE_DIR, cls.MODELS_DIR, cls.EVIDENCE_DIR]:
            if not os.path.exists(path):
                os.makedirs(path)


class DevelopmentConfig(Config):
    """Cấu hình dành cho môi trường phát triển"""

    DEBUG = True
    FLASK_ENV = "development"
    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY", "mtu_dev_secret_key_only_for_development"
    )
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    ALLOWED_ORIGINS = ["*"]


class ProductionConfig(Config):
    """Cấu hình dành cho môi trường sản phẩm"""

    DEBUG = False
    FLASK_ENV = "production"

    @classmethod
    def validate_config(cls):
        """Kiểm tra cấu hình bắt buộc khi chạy Production"""
        missing_or_default = []
        if not cls.SECRET_KEY or cls.SECRET_KEY in (
            "mtu_super_secret_key_2026",
            "mtu_dev_secret_key_only_for_development",
        ):
            missing_or_default.append("FLASK_SECRET_KEY")
        if not cls.JWT_SECRET_KEY or cls.JWT_SECRET_KEY in (
            "mtu_super_secret_key_2026",
            "mtu_dev_secret_key_only_for_development",
        ):
            missing_or_default.append("JWT_SECRET_KEY")
        if not cls.DB_PASSWORD:
            missing_or_default.append("DB_PASSWORD")
        if missing_or_default:
            raise RuntimeError(
                f"[SECURITY ERROR] Từ chối khởi động Production do thiếu hoặc dùng cấu hình mặc định cho: {', '.join(missing_or_default)}."
            )


# Mapping tên cấu hình
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,
}
