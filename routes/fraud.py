from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request,
    jsonify,
)
from db.connection import execute_query, execute_update, execute_one

fraud_bp = Blueprint("fraud", __name__, url_prefix="/fraud")

from utils.decorators import login_required


@fraud_bp.route("/", methods=["GET"])
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
    # Get all fraud logs
    sql = """
        SELECT g.*, s.ho_ten, s.mssv, l.ma_lop 
        FROM gian_lan_log g
        LEFT JOIN sinh_vien s ON g.sinh_vien_id = s.id
        LEFT JOIN lop_hoc l ON s.lop_id = l.id
        ORDER BY g.thoi_gian DESC
    """
    alerts = execute_query(sql)
    return render_template("dashboard/fraud_alerts.html", alerts=alerts)


@fraud_bp.route("/mark_resolved/<int:alert_id>", methods=["POST"])
def mark_resolved(alert_id):
    """
    /mark_resolved/<int:alert_id>
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    if "admin_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    sql = "UPDATE gian_lan_log SET da_xu_ly = 1 WHERE id = %s"
    res = execute_update(sql, (alert_id,))
    if res != -1:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Update failed"}), 500


@fraud_bp.route("/delete/<int:alert_id>", methods=["POST"])
def delete_alert(alert_id):
    """
    /delete/<int:alert_id>
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    if "admin_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    sql = "DELETE FROM gian_lan_log WHERE id = %s"
    res = execute_update(sql, (alert_id,))
    if res != -1:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Delete failed"}), 500


@fraud_bp.route("/api/report", methods=["POST"])
def report_fraud_api():
    """
    API cho Mobile App gọi lên khi phát hiện Fake GPS hoặc gian lận khác
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
    """
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Thiếu dữ liệu"}), 400

    sinh_vien_id = data.get("sinh_vien_id")
    loai_gian_lan = data.get("loai_gian_lan")  # e.g. "Fake GPS"
    chi_tiet = data.get("chi_tiet", "")

    if not loai_gian_lan:
        return jsonify({"success": False, "message": "Thiếu loại gian lận"}), 400

    sql = """
        INSERT INTO gian_lan_log (sinh_vien_id, loai_gian_lan, chi_tiet)
        VALUES (%s, %s, %s)
    """
    res = execute_update(sql, (sinh_vien_id, loai_gian_lan, chi_tiet))
    if res != -1:
        return jsonify({"success": True, "message": "Đã ghi nhận hành vi gian lận"})
    return jsonify({"success": False, "message": "Lỗi server"}), 500


@fraud_bp.route("/cancel_attendance/<int:alert_id>", methods=["POST"])
def cancel_attendance(alert_id):
    if "admin_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    log = execute_one(
        "SELECT sinh_vien_id, thoi_gian FROM gian_lan_log WHERE id = %s", (alert_id,)
    )
    if not log or not log["sinh_vien_id"]:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Không tìm thấy thông tin gian lận hoặc sinh viên không xác định",
                }
            ),
            404,
        )

    date_str = log["thoi_gian"].strftime("%Y-%m-%d")
    sv_id = log["sinh_vien_id"]

    sql = "DELETE FROM diem_danh WHERE sinh_vien_id = %s AND DATE(thoi_gian) = %s"
    res = execute_update(sql, (sv_id, date_str))

    if res != -1:
        execute_update(
            "UPDATE gian_lan_log SET da_xu_ly = 1 WHERE id = %s", (alert_id,)
        )
        return jsonify(
            {"success": True, "message": f"Đã hủy toàn bộ điểm danh ngày {date_str}"}
        )
    return jsonify({"success": False, "message": "Lỗi hệ thống"}), 500


@fraud_bp.route("/lock_account/<int:alert_id>", methods=["POST"])
def lock_account(alert_id):
    if "admin_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    log = execute_one(
        "SELECT sinh_vien_id FROM gian_lan_log WHERE id = %s", (alert_id,)
    )
    if not log or not log["sinh_vien_id"]:
        return (
            jsonify(
                {"success": False, "message": "Không tìm thấy thông tin sinh viên"}
            ),
            404,
        )

    sv_id = log["sinh_vien_id"]

    sv = execute_one("SELECT is_locked FROM sinh_vien WHERE id = %s", (sv_id,))
    if not sv:
        return jsonify({"success": False, "message": "Sinh viên không tồn tại"}), 404

    new_status = 0 if sv.get("is_locked") == 1 else 1

    sql = "UPDATE sinh_vien SET is_locked = %s WHERE id = %s"
    res = execute_update(sql, (new_status, sv_id))

    if res != -1:
        execute_update(
            "UPDATE gian_lan_log SET da_xu_ly = 1 WHERE id = %s", (alert_id,)
        )
        status_msg = "đã bị khóa" if new_status == 1 else "đã được mở khóa"
        return jsonify(
            {
                "success": True,
                "message": f"Tài khoản {status_msg}",
                "is_locked": new_status,
            }
        )
    return jsonify({"success": False, "message": "Không thể cập nhật trạng thái"}), 500
