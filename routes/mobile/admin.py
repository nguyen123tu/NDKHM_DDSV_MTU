"""
Mobile Admin API routes.
"""

import os
import shutil
from flask import request, jsonify, current_app
from db.connection import execute_query, execute_update
from . import api_mobile_bp
from .helpers import _require_mobile_auth


@api_mobile_bp.route("/admin/students", methods=["GET"])
def mobile_admin_get_students():
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get("role") != "admin":
            return jsonify({"success": False, "message": "Access Denied"}), 403

        query = request.args.get("q", "").strip()
        sql = """
            SELECT sv.id, sv.ho_ten, sv.mssv, sv.trang_thai, sv.sdt, sv.email, l.ma_lop
            FROM sinh_vien sv
            LEFT JOIN lop_hoc l ON sv.lop_id = l.id
        """
        params = []
        if query:
            sql += " WHERE sv.ho_ten LIKE %s OR sv.mssv LIKE %s"
            params = [f"%{query}%", f"%{query}%"]
        sql += " ORDER BY sv.ho_ten ASC OFFSET 0 ROWS FETCH NEXT 100 ROWS ONLY"

        students = execute_query(sql, tuple(params))
        return jsonify({"success": True, "data": students}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/admin/students/<int:student_id>", methods=["PUT"])
def mobile_admin_update_student(student_id):
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get("role") != "admin":
            return jsonify({"success": False, "message": "Access Denied"}), 403

        data = request.get_json() or {}
        ho_ten = data.get("ho_ten", "").strip()
        mssv = data.get("mssv", "").strip()
        ma_lop = data.get("ma_lop", "").strip()
        email = data.get("email", "").strip()
        sdt = data.get("sdt", "").strip()

        if not ho_ten or not mssv:
            return (
                jsonify(
                    {"success": False, "message": "Họ tên và MSSV không được để trống"}
                ),
                400,
            )

        exist = execute_query(
            "SELECT id FROM sinh_vien WHERE mssv = %s AND id != %s", (mssv, student_id)
        )
        if exist:
            return jsonify({"success": False, "message": "MSSV đã tồn tại"}), 400

        lop_id = None
        if ma_lop:
            lop = execute_query("SELECT id FROM lop_hoc WHERE ma_lop = %s", (ma_lop,))
            if lop:
                lop_id = lop[0]["id"]

        execute_update(
            """
            UPDATE sinh_vien 
            SET ho_ten=%s, mssv=%s, lop_id=%s, email=%s, sdt=%s 
            WHERE id=%s
        """,
            (ho_ten, mssv, lop_id, email, sdt, student_id),
        )

        return jsonify({"success": True, "message": "Cập nhật thành công"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/admin/students/<int:student_id>", methods=["DELETE"])
def mobile_admin_delete_student(student_id):
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get("role") != "admin":
            return jsonify({"success": False, "message": "Access Denied"}), 403

        execute_update("DELETE FROM sinh_vien WHERE id = %s", (student_id,))

        return jsonify({"success": True, "message": "Đã xóa sinh viên"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/admin/students/<int:student_id>/reset-face", methods=["POST"])
def mobile_admin_reset_face(student_id):
    try:
        payload, auth_error = _require_mobile_auth()
        if auth_error:
            return auth_error
        if payload.get("role") != "admin":
            return jsonify({"success": False, "message": "Access Denied"}), 403

        sv = execute_query("SELECT mssv FROM sinh_vien WHERE id=%s", (student_id,))
        if not sv:
            return (
                jsonify({"success": False, "message": "Không tìm thấy sinh viên"}),
                404,
            )

        mssv = sv[0]["mssv"]
        execute_update(
            "UPDATE sinh_vien SET trang_thai_face=0, face_vector=NULL WHERE id=%s",
            (student_id,),
        )

        dataset_path = os.path.join(current_app.root_path, "dataset", mssv)
        if os.path.exists(dataset_path):
            shutil.rmtree(dataset_path)

        return jsonify({"success": True, "message": "Đã xóa dữ liệu khuôn mặt"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@api_mobile_bp.route("/admin/leave-requests", methods=["GET"])
def mobile_admin_leave_requests():
    """Admin lấy danh sách tất cả đơn xin phép"""
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get("role") != "admin":
        return jsonify({"success": False, "message": "Chỉ Admin mới có quyền"}), 403

    status = request.args.get("status", type=int)
    from services.leave_service import get_all_leave_requests

    reqs = get_all_leave_requests(status)

    for r in reqs:
        if r.get("thoi_gian_tao"):
            r["thoi_gian_tao"] = r["thoi_gian_tao"].strftime("%Y-%m-%d %H:%M:%S")

    return jsonify({"success": True, "data": reqs}), 200


@api_mobile_bp.route("/admin/approve-leave/<int:request_id>", methods=["POST"])
def mobile_admin_approve_leave(request_id):
    """Admin duyệt đơn xin phép"""
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get("role") != "admin":
        return jsonify({"success": False, "message": "Chỉ Admin mới có quyền"}), 403

    from services.leave_service import update_leave_status

    if update_leave_status(request_id, 1) > 0:
        return jsonify({"success": True, "message": "Đã duyệt đơn"}), 200
    return jsonify({"success": False, "message": "Lỗi cập nhật"}), 500


@api_mobile_bp.route("/admin/reject-leave/<int:request_id>", methods=["POST"])
def mobile_admin_reject_leave(request_id):
    """Admin từ chối đơn xin phép"""
    payload, auth_error = _require_mobile_auth()
    if auth_error:
        return auth_error
    if payload.get("role") != "admin":
        return jsonify({"success": False, "message": "Chỉ Admin mới có quyền"}), 403

    from services.leave_service import update_leave_status

    if update_leave_status(request_id, 2) > 0:
        return jsonify({"success": True, "message": "Đã từ chối đơn"}), 200
    return jsonify({"success": False, "message": "Lỗi cập nhật"}), 500
