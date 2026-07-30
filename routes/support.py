from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import logging
from db.connection import execute_query, execute_update, execute_one

logger = logging.getLogger(__name__)
support_bp = Blueprint('support', __name__)

@support_bp.route('/')
def index():
    if not session.get('admin_id'):
        return redirect(url_for('auth.login'))
        
    # Lấy danh sách yêu cầu hỗ trợ
    requests = execute_query("""
        SELECT y.*, s.ho_ten, s.lop_id, l.ten_lop 
        FROM yeu_cau_ho_tro y
        JOIN sinh_vien s ON y.mssv = s.mssv
        LEFT JOIN lop_hoc l ON s.lop_id = l.id
        ORDER BY 
            CASE WHEN y.trang_thai = 'Chờ xử lý' THEN 1 ELSE 2 END,
            y.thoi_gian DESC
    """)
    
    return render_template('dashboard/support.html', requests=requests, active_page='support')

@support_bp.route('/resolve/<int:req_id>', methods=['POST'])
def resolve(req_id):
    if not session.get('admin_id'):
        return jsonify({"success": False, "msg": "Unauthorized: Vui lòng đăng nhập"}), 401
    if session.get('admin_role') != 'admin':
        return jsonify({"success": False, "msg": "Forbidden: Yêu cầu quyền Quản trị (Admin)"}), 403
        
    try:
        execute_update("UPDATE yeu_cau_ho_tro SET trang_thai = 'Đã giải quyết' WHERE id = %s", (req_id,))
        return jsonify({"success": True, "msg": "Đã đánh dấu giải quyết"})
    except Exception as e:
        logger.exception("Error resolving support request ID %s: %s", req_id, e)
        return jsonify({"success": False, "msg": "Lỗi nội bộ hệ thống"}), 500

@support_bp.route('/delete/<int:req_id>', methods=['POST'])
def delete(req_id):
    if not session.get('admin_id'):
        return jsonify({"success": False, "msg": "Unauthorized: Vui lòng đăng nhập"}), 401
    if session.get('admin_role') != 'admin':
        return jsonify({"success": False, "msg": "Forbidden: Yêu cầu quyền Quản trị (Admin)"}), 403
        
    try:
        execute_update("DELETE FROM yeu_cau_ho_tro WHERE id = %s", (req_id,))
        return jsonify({"success": True, "msg": "Đã xóa yêu cầu"})
    except Exception as e:
        logger.exception("Error deleting support request ID %s: %s", req_id, e)
        return jsonify({"success": False, "msg": "Lỗi nội bộ hệ thống"}), 500
