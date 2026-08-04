#!/bin/bash
# ============================================================
# 🚀 Script Triển Khai MTUFace Lên VPS Ubuntu
# ============================================================
# CÁCH DÙNG:
#   chmod +x deploy.sh
#   ./deploy.sh
# ============================================================

set -e  # Dừng ngay nếu có lỗi

echo "========================================================"
echo "🚀 MTUFace — BẮT ĐẦU TRIỂN KHAI LÊN VPS"
echo "========================================================"

# ─── Bước 1: Cập nhật hệ thống ───────────────────────────────
echo ""
echo "📦 [1/5] Cập nhật hệ thống..."
sudo apt update && sudo apt upgrade -y

# ─── Bước 2: Cài Docker ──────────────────────────────────────
echo ""
echo "🐳 [2/5] Cài đặt Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "   ✅ Docker đã được cài đặt!"
else
    echo "   ✅ Docker đã có sẵn: $(docker --version)"
fi

# Cài Docker Compose plugin
if ! docker compose version &> /dev/null; then
    sudo apt install docker-compose-plugin -y
    echo "   ✅ Docker Compose plugin đã được cài!"
else
    echo "   ✅ Docker Compose đã có sẵn: $(docker compose version)"
fi

# ─── Bước 3: Cấu hình .env ───────────────────────────────────
echo ""
echo "⚙️  [3/5] Cấu hình biến môi trường..."
if [ ! -f .env ]; then
    cp .env.production .env
    echo "   📝 Đã tạo file .env từ .env.production"
    echo ""
    echo "   ⚠️  QUAN TRỌNG: Hãy sửa file .env với giá trị thực:"
    echo "      nano .env"
    echo ""
    echo "   Nhấn Enter sau khi đã sửa xong .env..."
    read -r
else
    echo "   ✅ File .env đã tồn tại"
fi

# ─── Bước 4: Build và chạy Docker ────────────────────────────
echo ""
echo "🏗️  [4/5] Build và khởi động Docker containers..."
docker compose up -d --build

echo ""
echo "   ⏳ Đợi MSSQL khởi động (khoảng 30-40 giây)..."
sleep 40

# ─── Bước 5: Khởi tạo Database ───────────────────────────────
echo ""
echo "🗄️  [5/5] Khởi tạo Database schema..."
docker compose exec app python -c "from db.connection import init_database; init_database()"

# ─── Hoàn tất ────────────────────────────────────────────────
echo ""
echo "========================================================"
echo "✅ TRIỂN KHAI THÀNH CÔNG!"
echo "========================================================"
echo ""
echo "🌐 Truy cập web:    http://$(hostname -I | awk '{print $1}')"
echo "🔌 API trực tiếp:   http://$(hostname -I | awk '{print $1}'):5001"
echo ""
echo "📋 Các lệnh hữu ích:"
echo "   Xem logs:          docker compose logs -f app"
echo "   Khởi động lại:     docker compose restart"
echo "   Dừng hệ thống:     docker compose down"
echo "   Cập nhật code:     git pull && docker compose up -d --build"
echo ""
echo "========================================================"
