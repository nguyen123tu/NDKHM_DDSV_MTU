function filterClasses() {
    const q = document.getElementById('classSearch').value.toLowerCase();
    document.querySelectorAll('.class-card').forEach(card => {
        const text = card.getAttribute('data-search') || '';
        card.style.display = text.includes(q) ? '' : 'none';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Tích hợp SweetAlert2 cho nút xóa lớp
    document.querySelectorAll('.form-delete-class').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const className = this.getAttribute('data-name') || 'lớp này';
            
            Swal.fire({
                title: 'Xóa lớp học?',
                text: `Bạn có chắc chắn muốn xóa lớp ${className} không? Dữ liệu sinh viên trong lớp có thể bị ảnh hưởng.`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#d33',
                cancelButtonColor: '#3085d6',
                confirmButtonText: '<i class="fas fa-trash-alt me-1"></i> Xóa',
                cancelButtonText: 'Hủy',
                background: 'var(--bg-card)',
                color: 'var(--text-primary)'
            }).then((result) => {
                if (result.isConfirmed) {
                    this.submit();
                }
            });
        });
    });
});