"""
Security Module
Chứa các hàm bảo mật: JWT, tính toán GPS, và Anti-Replay (Nonce)
"""
import math
import time
from datetime import datetime, timedelta
import jwt
from flask import request, jsonify
from config import Config
import threading

# Bộ nhớ tạm lưu trữ các Nonce đã sử dụng để chống Replay Attack
# Cấu trúc: { "nonce_string": expire_timestamp_float }
_used_nonces = {}
_nonce_lock = threading.Lock()

def calculate_distance(lat1, lon1, lat2, lon2):
    """Tính khoảng cách (mét) giữa 2 tọa độ GPS bằng công thức Haversine"""
    R = 6371e3
    phi1 = lat1 * math.pi / 180
    phi2 = lat2 * math.pi / 180
    delta_phi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180
    a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def make_token(user, is_student=False):
    """Tạo JWT cho mobile app."""
    payload = {
        "sub": str(user["id"]),
        "username": user["username"] if not is_student else user["mssv"],
        "role": user.get("role", "admin") if not is_student else "student",
        "exp": datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")

def extract_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()

def require_mobile_auth():
    """Kiểm tra JWT Token từ Header"""
    token = extract_bearer_token()
    if not token:
        return None, (jsonify({"success": False, "message": "Thiếu Bearer token"}), 401)
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, (jsonify({"success": False, "message": "Token đã hết hạn"}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({"success": False, "message": "Token không hợp lệ"}), 401)

def verify_nonce(nonce, timestamp_ms, max_age_seconds=10):
    """
    Kiểm tra Anti-Replay:
    1. Timestamp không được quá cũ (mặc định 10 giây).
    2. Nonce chưa từng được sử dụng trong khoảng thời gian này.
    """
    if not nonce or not timestamp_ms:
        return False, "Thiếu nonce hoặc timestamp (Yêu cầu bảo mật Anti-Replay)"
        
    try:
        ts_sec = float(timestamp_ms) / 1000.0
    except ValueError:
        return False, "Timestamp không hợp lệ"
        
    now = time.time()
    
    # 1. Kiểm tra độ trễ (Chống gửi gói tin cũ)
    if abs(now - ts_sec) > max_age_seconds:
        return False, f"Yêu cầu quá hạn (Vượt quá {max_age_seconds} giây). Có dấu hiệu Replay Attack!"
        
    # 2. Kiểm tra Nonce đã dùng chưa
    with _nonce_lock:
        # Dọn dẹp các nonce đã cũ trong bộ nhớ
        expired_keys = [k for k, exp in _used_nonces.items() if now > exp]
        for k in expired_keys:
            del _used_nonces[k]
            
        if nonce in _used_nonces:
            return False, "Mã Nonce đã được sử dụng. Có dấu hiệu Replay Attack!"
            
        # Lưu nonce với thời gian hết hạn
        _used_nonces[nonce] = now + max_age_seconds
        
    return True, None
