"""
Route Quản lý Sinh viên (CRUD)
"""

import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from . import students_bp
from utils.decorators import login_required
from utils.helpers import allowed_image
from services import student_service, class_service
from config import Config

import base64

@students_bp.route('/')
@login_required
def list_students():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    lop_id = request.args.get('lop_id', type=int)
    
    data = student_service.get_all(lop_id=lop_id, search=search, page=page)
    classes = class_service.get_all()
    
    return render_template('students/list.html', 
                          students=data['items'],
                          pagination=data,
                          classes=classes,
                          current_search=search,
                          current_lop_id=lop_id)

@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    classes = class_service.get_all()
    
    if request.method == 'POST':
        mssv = request.form.get('mssv')
        ho_ten = request.form.get('ho_ten')
        lop_id = request.form.get('lop_id', type=int)
        
        # Xử lý upload ảnh avatar
        avatar_filename = None
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '' and allowed_image(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                avatar_filename = f"{mssv}_avatar.{ext}"
                
                # Tạo thư mục cho sinh viên nếu chưa có
                student_dir = os.path.join(Config.DATABASE_DIR, mssv)
                os.makedirs(student_dir, exist_ok=True)
                
                # Lưu avatar vào trong luôn (Làm file số 0)
                file_path = os.path.join(student_dir, f"0.{ext}")
                file.save(file_path)
                avatar_filename = f"{mssv}/0.{ext}" # path tương đối
        
        data = {
            'mssv': mssv,
            'ho_ten': ho_ten,
            'email': request.form.get('email'),
            'sdt': request.form.get('sdt'),
            'lop_id': lop_id,
            'ngay_sinh': request.form.get('ngay_sinh') or None,
            'gioi_tinh': request.form.get('gioi_tinh', type=int),
            'avatar': avatar_filename
        }
        
        result = student_service.create(data)
        if result >= 0:
            flash(f"Thêm sinh viên '{ho_ten}' thành công", "success")
            return redirect(url_for('students.list_students'))
        else:
            flash("Có lỗi xảy ra, có thể MSSV đã tồn tại", "danger")
            
    return render_template('students/add.html', classes=classes)

@students_bp.route('/api/add', methods=['POST'])
@login_required
def api_add():
    data = request.json
    mssv = data.get('mssv')
    ho_ten = data.get('ho_ten')
    lop_id = data.get('lop_id')
    images = data.get('images', []) # array base64
    
    if not mssv or not ho_ten or not lop_id:
        return jsonify({'success': False, 'msg': 'Thiếu thông tin bắt buộc'})
        
    student_data = {
        'mssv': mssv,
        'ho_ten': ho_ten,
        'lop_id': int(lop_id),
        'avatar': f"{mssv}/0.jpg" if images else None # Set first image as avatar if available
    }
    
    # Save student to db
    student_id = student_service.create(student_data)
    if student_id < 0:
        return jsonify({'success': False, 'msg': 'MSSV đã tồn tại hoặc lỗi CSDL'})
        
    # Save images to folder
    if images:
        student_dir = os.path.join(Config.DATABASE_DIR, mssv)
        os.makedirs(student_dir, exist_ok=True)
        for idx, base64_str in enumerate(images):
            try:
                # Remove header 'data:image/jpeg;base64,' if exists
                if ',' in base64_str:
                    base64_str = base64_str.split(',')[1]
                img_data = base64.b64decode(base64_str)
                with open(os.path.join(student_dir, f"{idx}.jpg"), 'wb') as f:
                    f.write(img_data)
            except Exception as e:
                pass
                
    return jsonify({'success': True, 'msg': 'Thêm sinh viên và ảnh thành công'})


@students_bp.route('/<int:id>')
@login_required
def detail(id):
    student = student_service.get_by_id(id)
    if not student:
        flash("Không tìm thấy sinh viên", "warning")
        return redirect(url_for('students.list_students'))
        
    from services.attendance_service import get_student_history
    history = get_student_history(student['mssv'], limit=50)
    image_count = student_service.count_images(student['mssv'])
    
    return render_template('students/detail.html', 
                          student=student, 
                          history=history,
                          image_count=image_count)

@students_bp.route('/api/images/<mssv>')
@login_required
def api_images(mssv):
    student_dir = os.path.join(Config.DATABASE_DIR, mssv)
    if not os.path.exists(student_dir):
        return jsonify([])
    
    images = []
    for f in os.listdir(student_dir):
        if f.lower().endswith('.jpg') or f.lower().endswith('.png'):
            images.append(f"{mssv}/{f}")
    
    # Sort them nicely if they are numbered
    images.sort(key=lambda x: int(x.split('/')[-1].split('.')[0]) if x.split('/')[-1].split('.')[0].isdigit() else 999)
    return jsonify(images)
@students_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    student = student_service.get_by_id(id)
    if not student:
        flash("Không tìm thấy sinh viên", "warning")
        return redirect(url_for('students.list_students'))
        
    classes = class_service.get_all()
    
    if request.method == 'POST':
        data = {
            'ho_ten': request.form.get('ho_ten'),
            'email': request.form.get('email'),
            'sdt': request.form.get('sdt'),
            'lop_id': request.form.get('lop_id', type=int),
            'ngay_sinh': request.form.get('ngay_sinh') or None,
            'gioi_tinh': request.form.get('gioi_tinh', type=int)
        }
        
        # Xử lý upload ảnh mới
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '' and allowed_image(file.filename):
                mssv = student['mssv']
                ext = file.filename.rsplit('.', 1)[1].lower()
                student_dir = os.path.join(Config.DATABASE_DIR, mssv)
                os.makedirs(student_dir, exist_ok=True)
                
                # Ghi đè file 0
                file_path = os.path.join(student_dir, f"0.{ext}")
                file.save(file_path)
                data['avatar'] = f"{mssv}/0.{ext}"
        
        if student_service.update(id, data):
            flash("Cập nhật thành công", "success")
            return redirect(url_for('students.detail', id=id))
        else:
            flash("Cập nhật thất bại", "danger")
            
    return render_template('students/edit.html', student=student, classes=classes)

@students_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if student_service.delete(id):
        flash("Đã xóa sinh viên", "success")
    else:
        flash("Lỗi khi xóa", "danger")
    return redirect(url_for('students.list_students'))
