"""
Service: Xuất dữ liệu Excel và PDF.
Dùng openpyxl cho .xlsx, reportlab cho .pdf
"""

import io
from datetime import datetime

from db.connection import execute_query
from services import class_service


def to_excel(lop_id, date=None):
    """
    Tạo file Excel (.xlsx) điểm danh của lớp.
    
    Args:
        lop_id: ID lớp học
        date: Ngày cần xuất (YYYY-MM-DD), mặc định hôm nay
        
    Returns:
        bytes: Nội dung file Excel
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    lop = class_service.get_by_id(lop_id)
    if not lop:
        return None

    # Query dữ liệu điểm danh
    if date:
        date_filter = "DATE(dd.thoi_gian) = %s"
        params = (lop_id, date)
    else:
        date_filter = "DATE(dd.thoi_gian) = CURDATE()"
        date = datetime.now().strftime("%Y-%m-%d")
        params = (lop_id,)

    sql = f"""
        SELECT sv.mssv, sv.ho_ten, dd.thoi_gian, dd.trang_thai, dd.do_chinh_xac, dd.gio_vao_lop
        FROM sinh_vien sv
        LEFT JOIN diem_danh dd ON sv.id = dd.sinh_vien_id AND {date_filter}
        WHERE sv.lop_id = %s
        ORDER BY sv.mssv ASC
    """
    records = execute_query(sql, params)

    wb = Workbook()

    # === Sheet 1: Chi tiết điểm danh ===
    ws1 = wb.active
    ws1.title = "Điểm Danh"

    # Styles
    header_fill = PatternFill(start_color="6A3CBC", end_color="6A3CBC", fill_type="solid")
    header_font = Font(name="Arial", size=12, bold=True, color="FFFFFF")
    title_font = Font(name="Arial", size=16, bold=True, color="333333")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    # Tiêu đề
    # Header hệ thống
    ws1.merge_cells('A1:E1')
    ws1['A1'] = "HỆ THỐNG ĐIỂM DANH KHUÔN MẶT - MTUFACE"
    ws1['A1'].font = Font(name="Arial", size=11, bold=True, color="6A3CBC")
    ws1['A1'].alignment = Alignment(horizontal="left")

    # Tiêu đề
    ws1.merge_cells('A3:E3')
    ws1['A3'] = f"BẢNG ĐIỂM DANH - {lop.get('ten_lop', '')}".upper()
    ws1['A3'].font = title_font
    ws1['A3'].alignment = Alignment(horizontal="center")

    ws1.merge_cells('A4:E4')
    ws1['A4'] = f"Mã lớp: {lop.get('ma_lop', '')} | Ngày: {date} | GV: {lop.get('giao_vien', '')}"
    ws1['A4'].font = Font(name="Arial", size=12, italic=True)
    ws1['A4'].alignment = Alignment(horizontal="center")

    # Header hàng 6
    headers = ["STT", "MSSV", "Họ và Tên", "Giờ vào lớp", "Giờ điểm danh", "Đi trễ", "Trạng thái"]
    for col, header in enumerate(headers, 1):
        cell = ws1.cell(row=6, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws1.row_dimensions[6].height = 25

    # Data
    # Formatting for absent and present
    absent_font = Font(name="Arial", size=11, color="FF0000", bold=True)
    present_font = Font(name="Arial", size=11, color="008000")
    late_font = Font(name="Arial", size=11, color="E67E22", bold=True)
    
    for i, record in enumerate(records, 1):
        row = i + 6
        ws1.cell(row=row, column=1, value=i).border = thin_border
        ws1.cell(row=row, column=1).alignment = Alignment(horizontal="center")
        ws1.cell(row=row, column=2, value=record.get("mssv", "")).border = thin_border
        ws1.cell(row=row, column=3, value=record.get("ho_ten", "")).border = thin_border

        # Xử lý giờ vào lớp
        gio_vao_lop_td = record.get("gio_vao_lop")
        if gio_vao_lop_td is not None:
            total_seconds = int(gio_vao_lop_td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            gio_vao_str = f"{hours:02d}:{minutes:02d}"
            start_time_obj = datetime.strptime(gio_vao_str, "%H:%M").time()
        else:
            gio_vao_str = "07:00"
            from datetime import time as datetime_time
            start_time_obj = datetime_time(7, 0)
            
        ws1.cell(row=row, column=4, value=gio_vao_str).border = thin_border
        ws1.cell(row=row, column=4).alignment = Alignment(horizontal="center")

        thoi_gian = record.get("thoi_gian")
        if thoi_gian:
            ws1.cell(row=row, column=5, value=thoi_gian.strftime("%H:%M:%S")).border = thin_border
            ws1.cell(row=row, column=5).alignment = Alignment(horizontal="center")
            
            # Tính đi trễ
            di_tre_phut = 0
            target_dt = datetime.combine(thoi_gian.date(), start_time_obj)
            if thoi_gian > target_dt:
                di_tre_phut = int((thoi_gian - target_dt).total_seconds() / 60)
                
            if di_tre_phut > 0:
                ws1.cell(row=row, column=6, value=f"{di_tre_phut} phút").border = thin_border
                ws1.cell(row=row, column=6).font = late_font
                status_cell = ws1.cell(row=row, column=7, value="Đi trễ")
                status_cell.font = late_font
            else:
                ws1.cell(row=row, column=6, value="Đúng giờ").border = thin_border
                status_cell = ws1.cell(row=row, column=7, value="Có mặt")
                status_cell.font = present_font
                
            ws1.cell(row=row, column=6).alignment = Alignment(horizontal="center")
            status_cell.border = thin_border
            status_cell.alignment = Alignment(horizontal="center")
        else:
            ws1.cell(row=row, column=5, value="--:--:--").border = thin_border
            ws1.cell(row=row, column=5).alignment = Alignment(horizontal="center")
            ws1.cell(row=row, column=6, value="--").border = thin_border
            ws1.cell(row=row, column=6).alignment = Alignment(horizontal="center")
            
            status_cell = ws1.cell(row=row, column=7, value="Vắng mặt")
            status_cell.border = thin_border
            status_cell.font = absent_font
            status_cell.alignment = Alignment(horizontal="center")

    # Auto-width
    ws1.column_dimensions['A'].width = 6
    ws1.column_dimensions['B'].width = 18
    ws1.column_dimensions['C'].width = 25
    ws1.column_dimensions['D'].width = 12
    ws1.column_dimensions['E'].width = 15
    ws1.column_dimensions['F'].width = 12
    ws1.column_dimensions['G'].width = 15

    # === Sheet 2: Thống kê ===
    ws2 = wb.create_sheet("Thống Kê")
    summary = class_service.get_attendance_summary(lop_id, date)

    ws2['A1'] = "THỐNG KÊ ĐIỂM DANH"
    ws2['A1'].font = title_font

    stats_data = [
        ("Sĩ số lớp", summary["si_so"]),
        ("Có mặt", summary["co_mat"]),
        ("Vắng", summary["vang"]),
        ("Tỷ lệ chuyên cần", f"{summary['ty_le']}%"),
    ]
    for i, (label, value) in enumerate(stats_data, 3):
        ws2.cell(row=i, column=1, value=label).font = Font(bold=True)
        ws2.cell(row=i, column=2, value=value)

    # Xuất ra bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def to_pdf(lop_id, date=None):
    """
    Tạo file PDF điểm danh (cơ bản).
    
    Args:
        lop_id: ID lớp học
        date: Ngày xuất
        
    Returns:
        bytes: Nội dung file PDF
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    lop = class_service.get_by_id(lop_id)
    if not lop:
        return None

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # Query dữ liệu
    sql = """
        SELECT sv.mssv, sv.ho_ten, dd.thoi_gian, dd.trang_thai, dd.gio_vao_lop
        FROM sinh_vien sv
        LEFT JOIN diem_danh dd ON sv.id = dd.sinh_vien_id AND DATE(dd.thoi_gian) = %s
        WHERE sv.lop_id = %s
        ORDER BY sv.mssv ASC
    """
    records = execute_query(sql, (date, lop_id))

    # Tạo PDF
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elements = []

    # Tiêu đề
    elements.append(Paragraph("<b>HE THONG DIEM DANH KHUON MAT - MTUFACE</b>", styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))
    
    title_style = styles['Title']
    title_style.textColor = colors.HexColor('#6A3CBC')
    elements.append(Paragraph(f"<b>BANG DIEM DANH LOP HOC</b>", title_style))
    elements.append(Paragraph(f"<b><font size='14'>{lop.get('ten_lop', '')}</font></b>", styles['Title']))
    
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        f"<b>Ma lop:</b> {lop.get('ma_lop', '')} &nbsp;&nbsp;&nbsp;&nbsp; <b>Ngay:</b> {date} &nbsp;&nbsp;&nbsp;&nbsp; <b>Giang vien:</b> {lop.get('giao_vien', '')}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.8 * cm))

    # Bảng dữ liệu
    table_data = [["STT", "MSSV", "Ho va Ten", "Vao lop", "Diem danh", "Trang thai"]]
    for i, record in enumerate(records, 1):
        thoi_gian = record.get("thoi_gian")
        
        gio_vao_lop_td = record.get("gio_vao_lop")
        if gio_vao_lop_td is not None:
            total_seconds = int(gio_vao_lop_td.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            gio_vao_str = f"{hours:02d}:{minutes:02d}"
            from datetime import time as datetime_time
            start_time_obj = datetime_time(hours, minutes)
        else:
            gio_vao_str = "07:00"
            from datetime import time as datetime_time
            start_time_obj = datetime_time(7, 0)
            
        if thoi_gian:
            tg_str = thoi_gian.strftime("%H:%M:%S")
            # Tính đi trễ
            target_dt = datetime.combine(thoi_gian.date(), start_time_obj)
            if thoi_gian > target_dt:
                di_tre_phut = int((thoi_gian - target_dt).total_seconds() / 60)
                if di_tre_phut > 0:
                    trang_thai_str = f"Tre {di_tre_phut} p"
                else:
                    trang_thai_str = "Co mat"
            else:
                trang_thai_str = "Co mat"
        else:
            tg_str = "--:--:--"
            trang_thai_str = "Vang mat"
            
        table_data.append([
            str(i),
            record.get("mssv", ""),
            record.get("ho_ten", ""),
            gio_vao_str,
            tg_str,
            trang_thai_str
        ])

    if len(table_data) > 1:
        table = Table(table_data, colWidths=[1.2 * cm, 3.2 * cm, 4.5 * cm, 2.3 * cm, 3 * cm, 3.5 * cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6A3CBC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F0FF')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("Khong co du lieu diem danh.", styles['Normal']))

    # Chữ ký
    elements.append(Spacer(1, 2 * cm))
    sig_data = [
        ["", f"Ngay {date}"],
        ["Giao vien", "Nguoi lap bieu"],
        ["", ""],
        [lop.get("giao_vien", ""), "Admin"]
    ]
    sig_table = Table(sig_data, colWidths=[8 * cm, 8 * cm])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    output.seek(0)
    return output.getvalue()


def roster_to_excel(lop_id):
    """
    Xuất danh sách lớp trắng (Roster) để Giảng viên sử dụng ngoài hệ thống.
    Chỉ bao gồm: STT, MSSV, Họ Tên, Giới Tính, Ngày Sinh, Ghi Chú (trống).
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    lop = class_service.get_by_id(lop_id)
    if not lop:
        return None

    sql = """
        SELECT mssv, ho_ten, gioi_tinh, ngay_sinh
        FROM sinh_vien
        WHERE lop_id = %s AND trang_thai = 1
        ORDER BY mssv ASC
    """
    students = execute_query(sql, (lop_id,))

    wb = Workbook()
    ws = wb.active
    ws.title = "Danh Sách Lớp"

    header_fill = PatternFill(start_color="6A3CBC", end_color="6A3CBC", fill_type="solid")
    header_font = Font(name="Arial", size=12, bold=True, color="FFFFFF")
    title_font = Font(name="Arial", size=16, bold=True, color="333333")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    # Header hệ thống
    ws.merge_cells('A1:F1')
    ws['A1'] = "HỆ THỐNG ĐIỂM DANH KHUÔN MẶT - MTUFACE"
    ws['A1'].font = Font(name="Arial", size=11, bold=True, color="6A3CBC")
    ws['A1'].alignment = Alignment(horizontal="left")

    # Tiêu đề
    ws.merge_cells('A3:F3')
    ws['A3'] = f"DANH SÁCH SINH VIÊN - {lop.get('ten_lop', '')}".upper()
    ws['A3'].font = title_font
    ws['A3'].alignment = Alignment(horizontal="center")

    ws.merge_cells('A4:F4')
    ws['A4'] = f"Mã lớp: {lop.get('ma_lop', '')} | GV: {lop.get('giao_vien', '')} | Sĩ số: {len(students)}"
    ws['A4'].font = Font(name="Arial", size=11, italic=True)
    ws['A4'].alignment = Alignment(horizontal="center")

    headers = ["STT", "MSSV", "Họ và Tên", "Giới Tính", "Ngày Sinh", "Ghi Chú"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws.row_dimensions[6].height = 25

    for i, sv in enumerate(students, 1):
        row = i + 6
        ws.cell(row=row, column=1, value=i).border = thin_border
        ws.cell(row=row, column=2, value=sv.get("mssv", "")).border = thin_border
        ws.cell(row=row, column=3, value=sv.get("ho_ten", "")).border = thin_border

        gioi_tinh = sv.get("gioi_tinh")
        gt_str = "Nam" if gioi_tinh == 1 else ("Nữ" if gioi_tinh == 0 else "")
        ws.cell(row=row, column=4, value=gt_str).border = thin_border

        ngay_sinh = sv.get("ngay_sinh")
        ns_str = ngay_sinh.strftime("%d/%m/%Y") if ngay_sinh else ""
        ws.cell(row=row, column=5, value=ns_str).border = thin_border

        ws.cell(row=row, column=6, value="").border = thin_border

    ws.column_dimensions['A'].width = 6
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 20

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def monthly_matrix_to_excel(lop_id, month, year):
    """
    Xuất ma trận điểm danh theo tháng.
    Cột 1: STT, Cột 2: MSSV, Cột 3: Họ Tên, các cột tiếp theo là từng ngày trong tháng.
    Ô giao: X (Có mặt) hoặc V (Vắng).
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    import calendar

    lop = class_service.get_by_id(lop_id)
    if not lop:
        return None

    # Lấy danh sách sinh viên trong lớp
    students = execute_query(
        "SELECT id, mssv, ho_ten FROM sinh_vien WHERE lop_id = %s AND trang_thai = 1 ORDER BY mssv ASC",
        (lop_id,)
    )
    if not students:
        return None

    # Lấy toàn bộ dữ liệu điểm danh trong tháng
    attendance_sql = """
        SELECT sinh_vien_id, DATE(thoi_gian) as ngay, MIN(thoi_gian) as checkin_time
        FROM diem_danh
        WHERE lop_id = %s AND MONTH(thoi_gian) = %s AND YEAR(thoi_gian) = %s
        GROUP BY sinh_vien_id, DATE(thoi_gian)
    """
    records = execute_query(attendance_sql, (lop_id, month, year))

    # Tạo dict lookup: (sinh_vien_id, ngày) -> checkin_time
    present_dict = {}
    for r in records:
        ngay = r.get("ngay")
        if ngay:
            day = ngay.day if hasattr(ngay, 'day') else int(str(ngay).split('-')[2])
            present_dict[(r["sinh_vien_id"], day)] = r.get("checkin_time")

    # Số ngày trong tháng
    num_days = calendar.monthrange(year, month)[1]

    wb = Workbook()
    ws = wb.active
    ws.title = f"Tháng {month}"

    header_fill = PatternFill(start_color="6A3CBC", end_color="6A3CBC", fill_type="solid")
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    title_font = Font(name="Arial", size=14, bold=True, color="333333")
    present_font = Font(name="Arial", size=10, color="008000", bold=True)
    absent_font = Font(name="Arial", size=10, color="FF0000", bold=True)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    last_col = 3 + num_days + 1  # STT + MSSV + HoTen + days + Tong

    # Header hệ thống
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    ws['A1'] = "HỆ THỐNG ĐIỂM DANH KHUÔN MẶT - MTUFACE"
    ws['A1'].font = Font(name="Arial", size=11, bold=True, color="6A3CBC")
    ws['A1'].alignment = Alignment(horizontal="left")

    # Tiêu đề
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=last_col)
    ws['A3'] = f"BẢNG ĐIỂM DANH THÁNG {month}/{year} - {lop.get('ten_lop', '')}".upper()
    ws['A3'].font = title_font
    ws['A3'].alignment = Alignment(horizontal="center")

    ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column=last_col)
    ws['A4'] = f"Mã lớp: {lop.get('ma_lop', '')} | GV: {lop.get('giao_vien', '')}"
    ws['A4'].font = Font(name="Arial", size=11, italic=True)
    ws['A4'].alignment = Alignment(horizontal="center")

    # Header row 6
    headers = ["STT", "MSSV", "Họ và Tên"]
    for day in range(1, num_days + 1):
        headers.append(str(day))
    headers.append("Tổng vắng mặt")

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=6, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws.row_dimensions[6].height = 25

    # Tìm các ngày thực sự có lớp (có ít nhất 1 người điểm danh)
    active_days = set()
    for (_, day) in present_dict.keys():
        active_days.add(day)

    # Data rows
    for i, sv in enumerate(students, 1):
        row = i + 6
        ws.cell(row=row, column=1, value=i).border = thin_border
        ws.cell(row=row, column=2, value=sv.get("mssv", "")).border = thin_border
        ws.cell(row=row, column=3, value=sv.get("ho_ten", "")).border = thin_border

        total_absent = 0
        for day in range(1, num_days + 1):
            col = 3 + day
            cell = ws.cell(row=row, column=col)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")

            if (sv["id"], day) in present_dict:
                checkin_time = present_dict[(sv["id"], day)]
                cell.value = checkin_time.strftime("%H:%M") if checkin_time else "X"
                cell.font = present_font
            else:
                if day in active_days:
                    cell.value = "V"
                    cell.font = absent_font
                    total_absent += 1
                else:
                    cell.value = ""

        # Tổng vắng mặt
        total_cell = ws.cell(row=row, column=3 + num_days + 1, value=total_absent)
        total_cell.border = thin_border
        total_cell.alignment = Alignment(horizontal="center")
        total_cell.font = Font(name="Arial", size=10, bold=True, color="FF0000")

    # Column widths
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 24
    for day in range(1, num_days + 1):
        from openpyxl.utils import get_column_letter
        ws.column_dimensions[get_column_letter(3 + day)].width = 6

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def generate_filename(lop_id, date, ext):
    """Tạo tên file xuất dữ liệu."""
    lop = class_service.get_by_id(lop_id)
    ma_lop = lop.get("ma_lop", "UNKNOWN") if lop else "UNKNOWN"
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    return f"DiemDanh_{ma_lop}_{date}.{ext}"
