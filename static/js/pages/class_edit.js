function confirmDelete() {
        if(confirm("CẢNH BÁO: Hành động này sẽ xóa VĨNH VIỄN lớp học này khỏi CSDL. Sinh viên và lịch sử điểm danh thuộc lớp cũng sẽ bị ảnh hưởng. Bạn có chắc chắn?")) {
            document.getElementById("deleteForm").submit();
        }
    }