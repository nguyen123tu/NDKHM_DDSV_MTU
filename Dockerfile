# ============================================================
# Dockerfile: Hệ Thống Điểm Danh Nhận Diện Khuôn Mặt (Production)
# Non-root user & Gunicorn eventlet worker configuration
# ============================================================

FROM python:3.11-slim AS base

# Đặt biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    DEBIAN_FRONTEND=noninteractive \
    FLASK_ENV=production

# Cài đặt system dependencies cho OpenCV, InsightFace, PIL và database drivers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    fonts-liberation \
    freetds-dev \
    && rm -rf /var/lib/apt/lists/*

# Tạo nhóm và người dùng non-root (appuser:appgroup)
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin -c "Docker app user" appuser

# Tạo thư mục làm việc
WORKDIR /app

# Copy requirements trước để tận dụng Docker layer cache
COPY requirements.txt .
COPY requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Tạo và phân quyền cho các thư mục lưu dữ liệu, AI models và bằng chứng
RUN mkdir -p /app/database /app/models /app/static /app/evidence /app/dataset && \
    chown -R appuser:appgroup /app

# Chuyển sang non-root user
USER appuser

# Expose port 5001
EXPOSE 5001

# Health check (kiểm tra server production phản hồi HTTP 200/302)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/auth/login')" || exit 1

# Khởi chạy server production qua Gunicorn với worker Eventlet
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5001", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
