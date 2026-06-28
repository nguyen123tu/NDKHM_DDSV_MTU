# ============================================================
# Dockerfile: Hệ Thống Điểm Danh Nhận Diện Khuôn Mặt
# Multi-stage build để giữ image nhỏ gọn
# ============================================================

FROM python:3.11-slim AS base

# Đặt biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    DEBIAN_FRONTEND=noninteractive

# Cài đặt system dependencies cho OpenCV, InsightFace, PIL
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

# Tạo thư mục làm việc
WORKDIR /app

# Copy requirements trước để tận dụng Docker layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Tạo các thư mục cần thiết
RUN mkdir -p /app/database /app/models /app/static

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/auth/login')" || exit 1

# Entrypoint
CMD ["python", "app.py"]
