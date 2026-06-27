from db.connection import execute_query, execute_update, execute_one
from services.fcm_service import send_custom_notification

def create_leave_request(sinh_vien_id, lop_id, ly_do, minh_chung_url=None):
    sql = """
        INSERT INTO don_xin_phep (sinh_vien_id, lop_id, ly_do, minh_chung_url, trang_thai)
        VALUES (%s, %s, %s, %s, 0)
    """
    return execute_update(sql, (sinh_vien_id, lop_id, ly_do, minh_chung_url))

def get_student_leave_requests(sinh_vien_id):
    sql = """
        SELECT d.id, d.ly_do, d.minh_chung_url, d.trang_thai, d.thoi_gian_tao, l.ten_lop, l.ma_lop
        FROM don_xin_phep d
        JOIN lop_hoc l ON d.lop_id = l.id
        WHERE d.sinh_vien_id = %s
        ORDER BY d.thoi_gian_tao DESC
    """
    return execute_query(sql, (sinh_vien_id,))

def get_all_leave_requests(status=None):
    sql = """
        SELECT d.id, d.ly_do, d.minh_chung_url, d.trang_thai, d.thoi_gian_tao, 
               l.ten_lop, l.ma_lop,
               s.ho_ten, s.mssv, s.id as sinh_vien_id
        FROM don_xin_phep d
        JOIN lop_hoc l ON d.lop_id = l.id
        JOIN sinh_vien s ON d.sinh_vien_id = s.id
    """
    params = []
    if status is not None:
        sql += " WHERE d.trang_thai = %s"
        params.append(status)
        
    sql += " ORDER BY d.thoi_gian_tao DESC"
    return execute_query(sql, tuple(params))

def update_leave_status(request_id, status):
    """Cập nhật trạng thái và bắn thông báo cho sinh viên"""
    sql = "UPDATE don_xin_phep SET trang_thai = %s WHERE id = %s"
    res = execute_update(sql, (status, request_id))
    
    if res > 0:
        # Lấy mssv để báo notification
        info = execute_one("""
            SELECT s.mssv, l.ten_lop 
            FROM don_xin_phep d 
            JOIN sinh_vien s ON d.sinh_vien_id = s.id 
            JOIN lop_hoc l ON d.lop_id = l.id
            WHERE d.id = %s
        """, (request_id,))
        
        if info:
            if status == 1:
                send_custom_notification(
                    "Đơn xin phép được chấp nhận", 
                    f"Giảng viên đã đồng ý cho bạn nghỉ môn {info['ten_lop']}.",
                    [info['mssv']]
                )
            elif status == 2:
                send_custom_notification(
                    "Đơn xin phép bị từ chối", 
                    f"Đơn xin nghỉ môn {info['ten_lop']} của bạn đã bị từ chối.",
                    [info['mssv']]
                )
    return res
