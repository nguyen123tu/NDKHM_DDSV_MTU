import os
import subprocess
from flask import Flask, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename
import db_handler

app = Flask(__name__)
app.secret_key = "super_secret_key_mtu" # Dành cho flash messages

DATABASE_DIR = "database"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

app.config['UPLOAD_FOLDER'] = DATABASE_DIR
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def dashboard():
    stats = db_handler.get_dashboard_stats()
    return render_template("dashboard.html", stats=stats)

@app.route("/students")
def students():
    student_list = db_handler.get_all_students()
    return render_template("students.html", students=student_list)

@app.route("/add_student", methods=["POST"])
def add_student():
    ma_sv = request.form.get("ma_sv")
    ho_ten = request.form.get("ho_ten")
    
    if 'file_anh' not in request.files:
        flash("Chưa chọn file ảnh!", "danger")
        return redirect(url_for('students'))
        
    file = request.files['file_anh']
    if file.filename == '':
        flash("File ảnh rỗng!", "danger")
        return redirect(url_for('students'))
        
    if file and allowed_file(file.filename):
        # Lưu file ảnh trực tiếp thành tên trùng ma_sv để AI dễ phân tích
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{ma_sv}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Ghi vào DB
        success = db_handler.add_student(ma_sv, ho_ten, filename)
        if success:
            # GỌI SUBPROCESS CHẠY NGẦM VIỆC EXTRACT EMBEDDINGS (AUTO TRAINING)
            try:
                # Dùng Popen chạy ngầm để không làm treo trang web chờ lâu
                subprocess.Popen(["python", "02_face_training.py"])
                flash(f"Đã lên lịch AI Training cho {ho_ten}! Giao diện giám sát sẽ tự thu nhận não bộ sau vài giây.", "success")
            except Exception as e:
                flash(f"Lỗi kích hoạt Engine Train AI: {e}", "warning")
        else:
            flash("Lỗi kết nối CSDL, có thể trùng mã SV.", "warning")
            
        return redirect(url_for('students'))
    else:
        flash("Định dạng ảnh không được hỗ trợ. Chỉ dùng JPG/PNG.", "danger")
        return redirect(url_for('students'))

@app.route("/logs")
def logs():
    logs_list = db_handler.get_all_logs(limit=100) # Chỉ lấy 100 log mới nhất
    return render_template("logs.html", logs=logs_list)

if __name__ == "__main__":
    db_handler.init_database_if_not_exists()
    print("\n[INFO] Đã khởi động máy chủ Web Admin tại http://127.0.0.1:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
