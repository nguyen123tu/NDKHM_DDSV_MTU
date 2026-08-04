"""
Route Quản lý Camera (Glassmorphism UI)
"""

from flask import render_template, request, jsonify
from . import camera_mgmt_bp
from utils.decorators import login_required
from core.camera import get_camera_manager


@camera_mgmt_bp.route("/")
@login_required
def index():
    """
    /
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    return render_template("camera/manage.html")


@camera_mgmt_bp.route("/api/list")
@login_required
def list_cameras():
    """
    /api/list
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    # Fix cứng dữ liệu mẫu vì chưa code Database Camera Management hoàn chỉnh
    cam_manager = get_camera_manager()
    connected = cam_manager.list_connected()

    cams = [
        {
            "id": 0,
            "ten_cam": "Camera Laptop (Default)",
            "url_hoac_index": "0",
            "vi_tri": "Bàn GV",
            "is_connected": 0 in connected,
        }
    ]
    return jsonify({"cameras": cams})


@camera_mgmt_bp.route("/api/scan-usb")
@login_required
def scan_usb():
    """
    /api/scan-usb
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    manager = get_camera_manager()
    usb_cams = manager.list_available_usb(3)
    return jsonify({"available": usb_cams})
