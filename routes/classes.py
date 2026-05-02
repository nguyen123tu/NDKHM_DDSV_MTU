"""
Route Quản lý Lớp Học (CRUD)
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from . import classes_bp
from utils.decorators import login_required
from services import class_service

@classes_bp.route('/')
@login_required
def list_classes():
    classes = class_service.get_all(active_only=False)
    return render_template('classes/list.html', classes=classes)

@classes_bp.route('/schedule')
@login_required
def schedule():
    return render_template('classes/schedule.html')

@classes_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        data = {
            'ma_lop': request.form.get('ma_lop'),
            'ten_lop': request.form.get('ten_lop'),
            'khoa': request.form.get('khoa'),
            'hoc_ky': request.form.get('hoc_ky'),
            'nam_hoc': request.form.get('nam_hoc'),
            'giao_vien': request.form.get('giao_vien'),
            'mo_ta': request.form.get('mo_ta')
        }
        
        result = class_service.create(data)
        if result >= 0:
            flash(f"Thêm lớp '{data['ten_lop']}' thành công", "success")
            return redirect(url_for('classes.list_classes'))
        else:
            flash("Lỗi! Mã lớp có thể đã tồn tại.", "danger")
            
    return render_template('classes/add.html')

@classes_bp.route('/<int:id>')
@login_required
def detail(id):
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
def edit(id):
    cls = class_service.get_by_id(id)
    if not cls:
        flash("Không tìm thấy lớp", "warning")
        return redirect(url_for('classes.list_classes'))
        
    if request.method == 'POST':
        data = {
            'ten_lop': request.form.get('ten_lop'),
            'khoa': request.form.get('khoa'),
            'hoc_ky': request.form.get('hoc_ky'),
            'nam_hoc': request.form.get('nam_hoc'),
            'giao_vien': request.form.get('giao_vien'),
            'mo_ta': request.form.get('mo_ta'),
            'trang_thai': request.form.get('trang_thai', type=int)
        }
        
        if class_service.update(id, data):
            flash("Cập nhật thành công", "success")
            return redirect(url_for('classes.detail', id=id))
        else:
            flash("Cập nhật thất bại", "danger")
            
    return render_template('classes/edit.html', cls=cls)

@classes_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if class_service.delete(id):
        flash("Đã chuyển lớp vào trạng thái vô hiệu hóa", "info")
    else:
        flash("Xóa thất bại", "danger")
    return redirect(url_for('classes.list_classes'))

@classes_bp.route('/<int:id>/students/json')
@login_required
def students_json(id):
    """API lấy SV theo JSON để dùng cho select boxes"""
    students = class_service.get_students_in_class(id)
    return jsonify({"students": students})
