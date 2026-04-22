"""
Entrypoint gọn cho môi trường development.

Chạy:
    python run_server.py
"""

from app import app, socketio


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", True))
