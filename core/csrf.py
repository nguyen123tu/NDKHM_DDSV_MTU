"""
CSRF Protection Module
Bảo vệ chống tấn công giả mạo yêu cầu liên trang (CSRF) cho Web Dashboard.
Hỗ trợ xác thực CSRF Token và kiểm tra Same-Origin (OWASP Fetch Metadata / Origin / Referer),
giúp bảo vệ an toàn mà không làm gián đoạn các form hay AJAX request hợp lệ từ giao diện.
Các endpoint API (như /api/mobile/..., /chatbot/...) sử dụng JWT hoặc Token riêng được tự động loại trừ.
"""

import os
import secrets
from flask import request, session, jsonify, abort, current_app


def generate_csrf_token():
    """Tạo hoặc lấy CSRF token trong session của người dùng"""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def init_csrf(app):
    """Khởi tạo middleware CSRF cho ứng dụng Flask"""
    # Đưa csrf_token vào Jinja2 context để dùng trong form HTML: {{ csrf_token() }}
    app.jinja_env.globals["csrf_token"] = generate_csrf_token

    @app.before_request
    def csrf_protect():
        # Chỉ kiểm tra với các phương thức thay đổi dữ liệu
        if request.method not in ("POST", "PUT", "DELETE", "PATCH"):
            return

        path = request.path
        # Các endpoint API mobile, chatbot, public api sử dụng cơ chế bảo mật khác (JWT / Nonce / API Key)
        if (
            path.startswith("/api/")
            or path.startswith("/chatbot/")
            or path.startswith("/public/api/")
        ):
            return

        # 1. Kiểm tra CSRF token tường minh trong form, json hoặc header X-CSRFToken / X-CSRF-Token
        token = (
            request.form.get("csrf_token")
            or request.headers.get("X-CSRFToken")
            or request.headers.get("X-CSRF-Token")
            or (
                request.json.get("csrf_token")
                if request.is_json and isinstance(request.json, dict)
                else None
            )
        )
        expected_token = session.get("csrf_token")
        if not expected_token:
            expected_token = generate_csrf_token()

        # Nếu có token và khớp chính xác -> Cho phép hợp lệ
        if token and secrets.compare_digest(str(token), str(expected_token)):
            return

        # 2. Kiểm tra Same-Origin (OWASP Standard Defense chống CSRF)
        # Nếu request xuất phát nội bộ từ cùng origin (giao diện dashboard), cho phép
        sec_fetch_site = request.headers.get("Sec-Fetch-Site")
        if sec_fetch_site in ("same-origin", "same-site", "none"):
            return

        host_url = request.host_url.rstrip("/")
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        allowed_origins = [
            o.rstrip("/") for o in current_app.config.get("ALLOWED_ORIGINS", [])
        ]
        allowed_origins.append(host_url)
        allowed_origins.append("http://localhost:5001")
        allowed_origins.append("http://127.0.0.1:5001")

        if origin:
            origin_clean = origin.rstrip("/")
            if any(
                origin_clean == ao or origin_clean.endswith(ao)
                for ao in allowed_origins
            ):
                return
        elif referer:
            if any(referer.startswith(ao) for ao in allowed_origins):
                return
        elif not sec_fetch_site and not origin and not referer:
            # Request nội bộ hoặc từ local test không có header cross-origin
            return

        # 3. Từ chối nếu là yêu cầu Cross-Site trái phép
        if (
            request.is_json
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or "application/json" in request.headers.get("Accept", "")
        ):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Lỗi bảo mật CSRF: Token không hợp lệ hoặc đã hết hạn. Vui lòng tải lại trang.",
                    }
                ),
                403,
            )
        abort(403, description="Lỗi bảo mật CSRF: Token không hợp lệ.")
