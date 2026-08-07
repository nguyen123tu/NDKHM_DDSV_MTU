"""
Route Quản lý Camera (Glassmorphism UI)
"""

from flask import render_template, request, jsonify
from . import camera_mgmt_bp
from utils.decorators import login_required
from core.camera import get_camera_manager
from db.connection import execute_query, execute_update


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
    cam_manager = get_camera_manager()
    connected = cam_manager.list_connected()

    cameras_db = execute_query("SELECT * FROM camera WHERE trang_thai = 1") or []
    cams = []
    for c in cameras_db:
        # Check connection status
        cam_id = c["id"]
        is_conn = str(cam_id) in [str(x) for x in connected] or cam_id in connected
        
        cams.append(
            {
                "id": cam_id,
                "ten_cam": c.get("ten_cam"),
                "url_hoac_index": c.get("url_hoac_index"),
                "vi_tri": c.get("vi_tri", ""),
                "is_connected": is_conn,
                "loai": c.get("loai", "USB"),
            }
        )
    return jsonify({"cameras": cams})


@camera_mgmt_bp.route("/api/add", methods=["POST"])
@login_required
def add_camera():
    data = request.json or {}
    ten_cam = data.get("ten_cam")
    loai = data.get("loai", "USB")
    url_hoac_index = data.get("url_hoac_index")
    vi_tri = data.get("vi_tri", "")
    
    if not ten_cam or not url_hoac_index:
        return jsonify({"success": False, "message": "Thiếu thông tin bắt buộc"}), 400
        
    execute_update(
        "INSERT INTO camera (ten_cam, loai, url_hoac_index, vi_tri) VALUES (%s, %s, %s, %s)",
        (ten_cam, loai, url_hoac_index, vi_tri)
    )
    return jsonify({"success": True, "message": "Thêm camera thành công"})


@camera_mgmt_bp.route("/api/update/<int:cam_id>", methods=["POST"])
@login_required
def update_camera(cam_id):
    data = request.json or {}
    ten_cam = data.get("ten_cam")
    loai = data.get("loai", "USB")
    url_hoac_index = data.get("url_hoac_index")
    vi_tri = data.get("vi_tri", "")
    
    execute_update(
        "UPDATE camera SET ten_cam=%s, loai=%s, url_hoac_index=%s, vi_tri=%s WHERE id=%s",
        (ten_cam, loai, url_hoac_index, vi_tri, cam_id)
    )
    return jsonify({"success": True, "message": "Cập nhật camera thành công"})


@camera_mgmt_bp.route("/api/delete/<int:cam_id>", methods=["POST"])
@login_required
def delete_camera(cam_id):
    execute_update("UPDATE camera SET trang_thai=0 WHERE id=%s", (cam_id,))
    return jsonify({"success": True, "message": "Xóa camera thành công"})


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
