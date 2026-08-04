function confirmDelete() {
        if (confirm('CẢNH BÁO: Xóa lớp học sẽ làm mất toàn bộ danh sách sinh viên và lịch sử điểm danh của lớp này. Bạn có chắc chắn muốn xóa?')) {
            document.getElementById('deleteForm').submit();
        }
    }