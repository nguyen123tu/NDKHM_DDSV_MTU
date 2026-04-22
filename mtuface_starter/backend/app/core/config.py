import os
from pathlib import Path


class Settings:
    APP_NAME = "MTUface API"
    APP_ENV = os.getenv("APP_ENV", "development")
    API_PREFIX = "/api/v1"

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mtuface.db")
    FACE_THRESHOLD = float(os.getenv("FACE_THRESHOLD", "0.45"))

    EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "./evidence")
    INSIGHTFACE_MODEL = os.getenv("INSIGHTFACE_MODEL", "buffalo_l")
    INSIGHTFACE_DET_SIZE = (
        int(os.getenv("INSIGHTFACE_DET_W", "640")),
        int(os.getenv("INSIGHTFACE_DET_H", "640")),
    )

    BASE_DIR = Path(__file__).resolve().parents[2]


settings = Settings()
