import os
import sys
from datetime import datetime

# Setup Flask app context
from app import create_app
from services import export_service
from db.connection import execute_query

app = create_app()

with app.app_context():
    try:
        # Lấy thử 1 lớp học có trong DB
        lops = execute_query("SELECT id FROM lop_hoc LIMIT 1")
        if not lops:
            print("Không có lớp học nào trong CSDL để test.")
            sys.exit(0)
            
        lop_id = lops[0]['id']
        print(f"Testing export cho lớp ID: {lop_id}")
        
        # Test Excel
        excel_bytes = export_service.to_excel(lop_id)
        if excel_bytes:
            print(f"Export Excel thành công! Kích thước: {len(excel_bytes)} bytes")
        else:
            print("Export Excel trả về None")
            
        # Test PDF
        pdf_bytes = export_service.to_pdf(lop_id)
        if pdf_bytes:
            print(f"Export PDF thành công! Kích thước: {len(pdf_bytes)} bytes")
        else:
            print("Export PDF trả về None")
            
        # Test Roster
        roster_bytes = export_service.roster_to_excel(lop_id)
        if roster_bytes:
            print(f"Export Danh Sách Trống thành công! Kích thước: {len(roster_bytes)} bytes")
            
        # Test Monthly
        now = datetime.now()
        monthly_bytes = export_service.monthly_matrix_to_excel(lop_id, now.month, now.year)
        if monthly_bytes:
            print(f"Export Thống Kê Tháng thành công! Kích thước: {len(monthly_bytes)} bytes")

        print("Tất cả các hàm export chạy mượt mà, không gặp lỗi Exception!")
        
    except Exception as e:
        import traceback
        print("CÓ LỖI XẢY RA TRONG QUÁ TRÌNH EXPORT:")
        traceback.print_exc()
