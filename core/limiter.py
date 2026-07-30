"""
Rate Limiter Module for MTUFace
Cung cấp bộ giới hạn tần suất truy cập (Rate Limiting) cho Flask:
- Hỗ trợ Flask-Limiter nếu được cài đặt trong môi trường.
- Tự động fallback sang In-Memory Thread-Safe Rate Limiter khi Flask-Limiter chưa cài đặt,
  đảm bảo hệ thống luôn được bảo vệ chống Brute-Force & DoS.
"""

import time
import logging
from functools import wraps
from flask import request, jsonify, abort

logger = logging.getLogger(__name__)

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    FLASK_LIMITER_AVAILABLE = True
except ImportError:
    FLASK_LIMITER_AVAILABLE = False


class InMemoryRateLimiter:
    """
    In-Memory Thread-Safe Rate Limiter fallback.
    Hỗ trợ cú pháp limit("5 per minute"), limit("30/minute"), ...
    """
    def __init__(self):
        import threading
        self.lock = threading.Lock()
        self.history = {}  # { (endpoint, ip): [timestamp1, timestamp2, ...] }

    def _parse_limit(self, limit_str: str):
        parts = limit_str.lower().replace("per", "/").split("/")
        count = int(parts[0].strip())
        unit = parts[1].strip() if len(parts) > 1 else "minute"
        if unit.startswith("sec"):
            seconds = 1
        elif unit.startswith("min"):
            seconds = 60
        elif unit.startswith("hour"):
            seconds = 3600
        elif unit.startswith("day"):
            seconds = 86400
        else:
            seconds = 60
        return count, seconds

    def limit(self, limit_str: str):
        max_requests, window_seconds = self._parse_limit(limit_str)

        def decorator(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                ip = request.remote_addr or "127.0.0.1"
                endpoint = request.endpoint or fn.__name__
                key = (endpoint, ip)
                now = time.time()

                with self.lock:
                    timestamps = self.history.get(key, [])
                    # Lọc bỏ các request đã ngoài khung thời gian (sliding window)
                    timestamps = [t for t in timestamps if now - t < window_seconds]

                    if len(timestamps) >= max_requests:
                        logger.warning("Rate limit exceeded for IP %s on %s (%s)", ip, endpoint, limit_str)
                        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.path.startswith("/api/") or request.path.startswith("/chatbot/"):
                            return jsonify({
                                "success": False,
                                "message": f"Too many requests. Vui lòng thử lại sau ({limit_str})."
                            }), 429
                        abort(429, description="Quá nhiều yêu cầu. Vui lòng quay lại sau.")

                    timestamps.append(now)
                    self.history[key] = timestamps

                return fn(*args, **kwargs)
            return wrapped
        return decorator

    def init_app(self, app):
        logger.info("Initialized InMemoryRateLimiter fallback")


if FLASK_LIMITER_AVAILABLE:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000 per day", "200 per hour"]
    )
else:
    limiter = InMemoryRateLimiter()

def init_limiter(app):
    """Khởi tạo Rate Limiter cho ứng dụng Flask"""
    limiter.init_app(app)
