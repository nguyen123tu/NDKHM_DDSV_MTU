"""
Helper functions and common imports for Mobile API modules.
"""

import os
import uuid
import base64
import time
import math
import logging
from datetime import datetime, timedelta

import jwt
from flask import request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from db.connection import execute_one, execute_query, execute_update
from config import Config
from services import attendance_service
from services.telegram_alert import send_telegram_message
from core.image_validator import save_validated_image
from core.limiter import limiter

from core.security import (
    calculate_distance,
    make_token as _make_token,
    extract_bearer_token as _extract_bearer_token,
    require_mobile_auth as _require_mobile_auth,
    verify_nonce
)


def _save_evidence_image(image_b64, mssv):
    """
    Lưu ảnh base64 làm bằng chứng vào database/evidence/YYYYMMDD.
    Trả về relative path để lưu DB.
    """
    if not image_b64:
        return None

    raw = image_b64.strip()
    if "," in raw and raw.startswith("data:image"):
        raw = raw.split(",", 1)[1]

    image_bytes = base64.b64decode(raw)
    date_folder = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join(Config.EVIDENCE_DIR, date_folder)
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{mssv}_{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
    abs_path = os.path.join(save_dir, filename)

    try:
        save_validated_image(image_bytes, abs_path)
    except Exception as e:
        logging.warning("Failed to validate/save base64 evidence image: %s", e)
        return None

    rel_path = os.path.relpath(abs_path, Config.BASE_DIR).replace("\\", "/")
    return rel_path


def _save_multipart_image(file_obj, mssv):
    """Lưu ảnh từ multipart/form-data."""
    if file_obj is None:
        return None
    date_folder = datetime.now().strftime("%Y%m%d")
    save_dir = os.path.join(Config.EVIDENCE_DIR, date_folder)
    os.makedirs(save_dir, exist_ok=True)
    ext = os.path.splitext(file_obj.filename or "")[-1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    filename = f"{mssv}_{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    abs_path = os.path.join(save_dir, filename)
    try:
        save_validated_image(file_obj, abs_path)
    except Exception as e:
        logging.warning("Failed to validate/save multipart evidence image: %s", e)
        return None
    return os.path.relpath(abs_path, Config.BASE_DIR).replace("\\", "/")


def _is_within_checkin_window(session_start_str):
    """
    session_start_str format: YYYY-mm-dd HH:MM:SS
    Cho phép check-in trong khoảng [start-early, start+late].
    """
    if not session_start_str:
        return True, None
    try:
        start_time = datetime.strptime(session_start_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False, "session_start không đúng định dạng YYYY-mm-dd HH:MM:SS"

    now = datetime.now()
    early = timedelta(minutes=Config.MOBILE_ALLOWED_CHECKIN_EARLY_MIN)
    late = timedelta(minutes=Config.MOBILE_ALLOWED_CHECKIN_LATE_MIN)
    if now < (start_time - early) or now > (start_time + late):
        return False, "Ngoài khung giờ check-in cho phép"
    return True, None


def get_distance_meters(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0
    R = 6371000  # Bán kính Trái đất tính bằng mét
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
