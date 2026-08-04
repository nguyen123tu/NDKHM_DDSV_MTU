"""
Route xuất dữ liệu (Excel/PDF)
"""

from flask import render_template, request, send_file, flash, redirect, url_for
import io
from . import export_bp
from utils.decorators import login_required
from services import class_service, export_service


@export_bp.route("/")
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
    classes = class_service.get_all(active_only=False)
    return render_template("export/index.html", classes=classes)


@export_bp.route("/download", methods=["POST"])
@login_required
def download():
    """
    /download
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
      500:
        description: Lỗi máy chủ
    """
    lop_id = request.form.get("lop_id", type=int)
    date = request.form.get("date")
    fmt = request.form.get("format", "excel")

    if not lop_id:
        flash("Vui lòng chọn lớp học", "danger")
        return redirect(url_for("export.index"))

    try:
        if fmt == "excel":
            file_bytes = export_service.to_excel(lop_id, date)
            mimetype = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            ext = "xlsx"
        else:  # pdf
            file_bytes = export_service.to_pdf(lop_id, date)
            mimetype = "application/pdf"
            ext = "pdf"

        if not file_bytes:
            flash("Không có dữ liệu điểm danh", "warning")
            return redirect(url_for("export.index"))

        filename = export_service.generate_filename(lop_id, date, ext)

        return send_file(
            io.BytesIO(file_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        print(f"[EXPORT ERROR] {e}")
        flash("Lỗi xuất file", "danger")
        return redirect(url_for("export.index"))


@export_bp.route("/roster", methods=["POST"])
@login_required
def roster():
    """
    Xuất danh sách lớp trắng (Roster).
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
    """
    lop_id = request.form.get("lop_id", type=int)

    if not lop_id:
        flash("Vui lòng chọn lớp học", "danger")
        return redirect(url_for("export.index"))

    try:
        file_bytes = export_service.roster_to_excel(lop_id)
        if not file_bytes:
            flash("Lớp học không có sinh viên nào", "warning")
            return redirect(url_for("export.index"))

        lop = class_service.get_by_id(lop_id)
        ma_lop = lop.get("ma_lop", "UNKNOWN") if lop else "UNKNOWN"
        filename = f"DanhSach_{ma_lop}.xlsx"

        return send_file(
            io.BytesIO(file_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        print(f"[ROSTER EXPORT ERROR] {e}")
        flash("Lỗi xuất danh sách lớp", "danger")
        return redirect(url_for("export.index"))


@export_bp.route("/monthly", methods=["POST"])
@login_required
def monthly():
    """
    Xuất ma trận điểm danh theo tháng.
    ---
    tags:
      - Web API
    responses:
      200:
        description: Thành công
    """
    lop_id = request.form.get("lop_id", type=int)
    month = request.form.get("month", type=int)
    year = request.form.get("year", type=int)

    if not lop_id or not month or not year:
        flash("Vui lòng chọn đầy đủ lớp, tháng, năm", "danger")
        return redirect(url_for("export.index"))

    try:
        file_bytes = export_service.monthly_matrix_to_excel(lop_id, month, year)
        if not file_bytes:
            flash("Không có dữ liệu hoặc lớp không có sinh viên", "warning")
            return redirect(url_for("export.index"))

        lop = class_service.get_by_id(lop_id)
        ma_lop = lop.get("ma_lop", "UNKNOWN") if lop else "UNKNOWN"
        filename = f"DiemDanh_{ma_lop}_Thang{month}_{year}.xlsx"

        return send_file(
            io.BytesIO(file_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        print(f"[MONTHLY EXPORT ERROR] {e}")
        flash("Lỗi xuất báo cáo tháng", "danger")
        return redirect(url_for("export.index"))


@export_bp.route("/session/<int:phien_id>", methods=["GET"])
@login_required
def export_session(phien_id):
    """Xuất file Excel báo cáo chi tiết theo phiên điểm danh."""
    try:
        file_bytes = export_service.export_session_report(phien_id)
        if not file_bytes:
            flash("Không tìm thấy phiên hoặc phiên không có dữ liệu", "warning")
            return redirect(url_for("export.index"))

        filename = f"BaoCao_Phien_{phien_id}.xlsx"
        return send_file(
            io.BytesIO(file_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        print(f"[SESSION EXPORT ERROR] {e}")
        flash("Lỗi xuất báo cáo phiên", "danger")
        return redirect(url_for("export.index"))


@export_bp.route("/semester", methods=["POST"])
@login_required
def export_semester():
    """Xuất ma trận chuyên cần cả học kỳ (tất cả các phiên đã chốt) của lớp."""
    lop_id = request.form.get("lop_id", type=int)
    if not lop_id:
        flash("Vui lòng chọn lớp học", "danger")
        return redirect(url_for("export.index"))

    try:
        file_bytes = export_service.export_semester_report(lop_id)
        if not file_bytes:
            flash(
                "Lớp chưa có phiên điểm danh nào đã chốt hoặc không có sinh viên",
                "warning",
            )
            return redirect(url_for("export.index"))

        lop = class_service.get_by_id(lop_id)
        ma_lop = lop.get("ma_lop", "UNKNOWN") if lop else "UNKNOWN"
        filename = f"ChuyenCan_HocKy_{ma_lop}.xlsx"
        return send_file(
            io.BytesIO(file_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        print(f"[SEMESTER EXPORT ERROR] {e}")
        flash("Lỗi xuất báo cáo học kỳ", "danger")
        return redirect(url_for("export.index"))
