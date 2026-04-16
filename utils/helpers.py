"""
Utils: Helpers cho toàn hệ thống.
"""

import math
from datetime import datetime

def remove_accents(input_str):
    """
    Loại bỏ dấu tiếng Việt khỏi chuỗi.
    Dùng để hiển thị lên video frame (OpenCV không hỗ trợ UTF-8 mặc định).
    """
    if not input_str:
        return ""
    
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    s = ""
    for c in input_str:
        if c in s1:
            s += s0[s1.index(c)]
        else:
            s += c
    return s

def format_datetime(dt, fmt='%H:%M %d/%m/%Y'):
    """
    Format datetime object sang chuỗi.
    """
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            # Nếu truyền vào là string từ DB
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return dt
    return dt.strftime(fmt)

def paginate(query_result, page, per_page):
    """
    Logic tính toán phân trang (nếu backend không DB count).
    (Thường nên paginate bằng query SQL, dùng hàm này cho fallback)
    """
    total = len(query_result)
    pages = math.ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    items = query_result[start:end]
    
    return {
        "items": items,
        "total": total,
        "pages": pages,
        "current": page
    }

def allowed_image(filename):
    """
    Kiểm tra phần mở rộng file ảnh có hợp lệ không.
    """
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
