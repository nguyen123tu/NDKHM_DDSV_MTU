"""
Route Quản lý Lớp Học (CRUD)
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from . import classes_bp
from utils.decorators import login_required, admin_required
from services import class_service

@classes_bp.route('/')
@login_required
def list_classes():
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
    classes = class_service.get_all(active_only=False)
    return render_template('classes/list.html', classes=classes)

@classes_bp.route('/schedule')
@login_required
def schedule():
    """
    /schedule
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    return render_template('classes/schedule.html')

@classes_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    from db.connection import execute_query
    giang_viens = execute_query("SELECT id, ho_ten FROM admin WHERE role = 'giang_vien'")
    
    if request.method == 'POST':
        data = {
            'ma_lop': request.form.get('ma_lop'),
            'ten_lop': request.form.get('ten_lop'),
            'khoa': request.form.get('khoa'),
            'hoc_ky': request.form.get('hoc_ky'),
            'nam_hoc': request.form.get('nam_hoc'),
            'giang_vien_id': request.form.get('giang_vien_id', type=int),
            'giao_vien': request.form.get('giao_vien'), # Dùng làm ghi chú tên nếu cần
            'mo_ta': request.form.get('mo_ta')
        }
        
        result = class_service.create(data)
        if result >= 0:
            flash(f"Thêm lớp '{data['ten_lop']}' thành công", "success")
            return redirect(url_for('classes.list_classes'))
        else:
            flash("Lỗi! Mã lớp có thể đã tồn tại.", "danger")
            
    return render_template('classes/add.html', giang_viens=giang_viens)

@classes_bp.route('/<int:id>')
@login_required
def detail(id):
    """
    /<int:id>
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    cls = class_service.get_by_id(id)
    if not cls:
        flash("Không tìm thấy lớp học", "warning")
        return redirect(url_for('classes.list_classes'))
        
    students = class_service.get_students_in_class(id)
    summary = class_service.get_attendance_summary(id)
    
    return render_template('classes/detail.html', 
                          cls=cls, 
                          students=students,
                          summary=summary)

@classes_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    cls = class_service.get_by_id(id)
    if not cls:
        flash("Không tìm thấy lớp", "warning")
        return redirect(url_for('classes.list_classes'))
        
    from db.connection import execute_query
    giang_viens = execute_query("SELECT id, ho_ten FROM admin WHERE role = 'giang_vien'")
        
    if request.method == 'POST':
        data = {
            'ten_lop': request.form.get('ten_lop'),
            'khoa': request.form.get('khoa'),
            'hoc_ky': request.form.get('hoc_ky'),
            'nam_hoc': request.form.get('nam_hoc'),
            'giang_vien_id': request.form.get('giang_vien_id', type=int),
            'giao_vien': request.form.get('giao_vien'),
            'mo_ta': request.form.get('mo_ta'),
            'trang_thai': request.form.get('trang_thai', type=int)
        }
        
        if class_service.update(id, data):
            flash("Cập nhật thành công", "success")
            return redirect(url_for('classes.detail', id=id))
        else:
            flash("Cập nhật thất bại", "danger")
            
    schedules = class_service.get_schedule(id)
    return render_template('classes/edit.html', cls=cls, schedules=schedules, giang_viens=giang_viens)

@classes_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """
    /<int:id>/delete
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    if class_service.delete(id):
        flash("Đã chuyển lớp vào trạng thái vô hiệu hóa", "info")
    else:
        flash("Xóa thất bại", "danger")
    return redirect(url_for('classes.list_classes'))

@classes_bp.route('/<int:id>/students/json')
@login_required
def students_json(id):
    """
    API lấy SV theo JSON để dùng cho select boxes
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
    """
    students = class_service.get_students_in_class(id)
    return jsonify({"students": students})

@classes_bp.route('/<int:id>/schedule/add', methods=['POST'])
@login_required
def schedule_add(id):
    """
    API thêm lịch học cho lớp
    """
    thu = request.form.get('thu', type=int)
    gio_bat_dau = request.form.get('gio_bat_dau')
    gio_ket_thuc = request.form.get('gio_ket_thuc')
    phong_hoc = request.form.get('phong_hoc')
    ghi_chu = request.form.get('ghi_chu')
    
    if not thu or not gio_bat_dau:
        flash("Thiếu thông tin Thứ hoặc Giờ bắt đầu", "danger")
        return redirect(url_for('classes.edit', id=id))
        
    class_service.add_schedule(id, thu, gio_bat_dau, gio_ket_thuc, phong_hoc, ghi_chu)
    flash("Thêm lịch học thành công", "success")
    return redirect(url_for('classes.edit', id=id))

@classes_bp.route('/<int:id>/schedule/<int:schedule_id>/delete', methods=['POST'])
@login_required
def schedule_delete(id, schedule_id):
    """
    API xóa lịch học của lớp
    """
    class_service.delete_schedule(schedule_id)
    flash("Xóa lịch học thành công", "success")
    return redirect(url_for('classes.edit', id=id))
