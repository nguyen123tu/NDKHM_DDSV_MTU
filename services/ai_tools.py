import json
from db.connection import execute_one, execute_query

# Định nghĩa các tool schemas theo chuẩn OpenAI Function Calling / NVIDIA NIM
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Tìm kiếm thông tin trong kho tri thức của dự án MTUFace. Sử dụng khi cần trả lời các câu hỏi về tài liệu, cách dùng hệ thống, hoặc kiến thức chung.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Câu truy vấn tìm kiếm"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_info",
            "description": "Tra cứu thông tin chi tiết của một sinh viên thông qua Mã Số Sinh Viên (MSSV), bao gồm số buổi vắng.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mssv": {
                        "type": "string",
                        "description": "Mã số sinh viên cần tra cứu. Ví dụ: '210001'",
                    }
                },
                "required": ["mssv"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_attendance_report",
            "description": "Xuất báo cáo điểm danh của một lớp học ra file Excel hoặc PDF.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ma_lop": {
                        "type": "string",
                        "description": "Mã lớp hoặc tên lớp cần xuất báo cáo. Ví dụ: 'CNTT1'",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["excel", "pdf"],
                        "description": "Định dạng file xuất (excel hoặc pdf)",
                    },
                    "date": {
                        "type": "string",
                        "description": "Ngày điểm danh (YYYY-MM-DD). Nếu không truyền sẽ lấy ngày hôm nay.",
                    },
                },
                "required": ["ma_lop", "format"],
            },
        },
    },
]


def execute_tool(tool_call, user_context=None):
    """
    Thực thi tool dựa trên thông tin tool_call từ LLM
    """
    func_name = tool_call.get("name")
    user_context = user_context or {}
    role = str(user_context.get("role") or "").lower()

    try:
        args_str = tool_call.get("arguments", "{}")
        # LLM có thể trả về arguments dưới dạng string hoặc dict
        if isinstance(args_str, str):
            args = json.loads(args_str)
        else:
            args = args_str
    except Exception as e:
        return f"Lỗi parse tham số: {str(e)}"

    print(f"[AI Agent] Thực thi tool: {func_name} với tham số {args}")

    if func_name == "search_knowledge":
        return _tool_search_knowledge(args.get("query", ""))

    elif func_name == "get_student_info":
        requested_mssv = str(args.get("mssv", "")).strip()
        if role == "student" and requested_mssv.lower() != str(
            user_context.get("username") or ""
        ).strip().lower():
            return "Bạn chỉ được phép tra cứu thông tin điểm danh của chính mình."
        if role not in ("student", "admin", "lecturer", "giang_vien"):
            return "Bạn cần đăng nhập để tra cứu thông tin sinh viên."
        return _tool_get_student_info(requested_mssv)

    elif func_name == "export_attendance_report":
        if role not in ("admin", "lecturer", "giang_vien"):
            return "Bạn không có quyền xuất báo cáo điểm danh."
        return _tool_export_report(
            args.get("ma_lop", ""), args.get("format", "excel"), args.get("date")
        )

    else:
        return f"Lỗi: Không tìm thấy tool '{func_name}'"


def _tool_search_knowledge(query: str) -> str:
    from services.knowledge_builder import get_knowledge_builder

    if not query:
        return "Không có truy vấn tìm kiếm."

    kb = get_knowledge_builder()
    results = kb.search(query, n_results=5)

    if not results:
        return "Không tìm thấy thông tin nào trong kho tri thức."

    parts = []
    for i, chunk in enumerate(results, 1):
        parts.append(
            f"--- Nguồn {i}: {chunk['source']} ({chunk['category']}) ---\n"
            f"{chunk['text']}\n"
        )
    return "\n".join(parts)


def _tool_get_student_info(mssv: str) -> str:
    if not mssv:
        return "Vui lòng cung cấp MSSV."

    sv = execute_one("SELECT * FROM sinh_vien WHERE mssv = %s", (mssv,))
    if not sv:
        return f"Không tìm thấy sinh viên nào có MSSV là {mssv}."

    lop = execute_one("SELECT ten_lop FROM lop_hoc WHERE id = %s", (sv["lop_id"],))
    ten_lop = lop["ten_lop"] if lop else "Không rõ"

    total_sessions = execute_one(
        "SELECT COUNT(*) as count FROM phien_diem_danh WHERE lop_id = %s",
        (sv["lop_id"],),
    )
    present = execute_one(
        "SELECT COUNT(*) as count FROM diem_danh WHERE sinh_vien_id = %s AND status IN ('PRESENT', 'LATE')",
        (sv["id"],),
    )

    vang = (total_sessions["count"] if total_sessions else 0) - (
        present["count"] if present else 0
    )
    if vang < 0:
        vang = 0

    return json.dumps(
        {
            "ho_ten": sv["ho_ten"],
            "mssv": sv["mssv"],
            "lop": ten_lop,
            "so_buoi_vang": vang,
            "trang_thai": "Hoạt động",
        },
        ensure_ascii=False,
    )


def _tool_export_report(ma_lop: str, fmt: str, date: str = None) -> str:
    from services import export_service
    from datetime import datetime
    import os

    if not ma_lop:
        return "Vui lòng cung cấp mã lớp."

    lop = execute_one(
        "SELECT id, ma_lop FROM lop_hoc WHERE ma_lop LIKE %s OR ten_lop LIKE %s",
        (f"%{ma_lop}%", f"%{ma_lop}%"),
    )
    if not lop:
        return f"Không tìm thấy lớp học nào có mã hoặc tên chứa '{ma_lop}'."

    lop_id = lop["id"]
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    try:
        if fmt == "excel":
            file_bytes = export_service.to_excel(lop_id, date)
            ext = "xlsx"
        else:
            file_bytes = export_service.to_pdf(lop_id, date)
            ext = "pdf"

        if not file_bytes:
            return "Không có dữ liệu điểm danh cho lớp này trong ngày được chọn."

        filename = export_service.generate_filename(lop_id, date, ext)

        exports_dir = os.path.join(os.path.dirname(__file__), "..", "static", "exports")
        os.makedirs(exports_dir, exist_ok=True)

        file_path = os.path.join(exports_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        url = f"/chatbot/download-export/{filename}"

        return (
            f"Báo cáo của lớp **{lop['ma_lop']}** ngày {date} đã sẵn sàng!\n\n"
            f"<a href='{url}' class='btn-download-card'>"
            f"<i class='fas fa-download'></i> Tải Báo Cáo ({ext.upper()})"
            f"</a>"
        )
    except Exception as e:
        return f"Đã xảy ra lỗi khi xuất báo cáo: {e}"
