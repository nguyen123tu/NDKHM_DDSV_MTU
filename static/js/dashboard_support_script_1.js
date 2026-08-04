function viewDetails(name, mssv, lop, title, content, time) {
        document.getElementById('detName').innerText = name;
        document.getElementById('detMssvClass').innerText = mssv + (lop ? ' - Lớp: ' + lop : '');
        document.getElementById('detTitle').innerText = title;
        document.getElementById('detContent').innerText = content;
        document.getElementById('detTime').innerText = time;
        new bootstrap.Modal(document.getElementById('detailModal')).show();
    }

    async function resolveRequest(id) {
        if (typeof Swal !== 'undefined') {
            const result = await Swal.fire({
                title: 'Giải quyết yêu cầu?',
                text: 'Đánh dấu yêu cầu này là Đã Giải Quyết?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonColor: '#10B981',
                cancelButtonColor: '#6c757d',
                confirmButtonText: '<i class="fas fa-check me-1"></i> Đồng ý',
                cancelButtonText: 'Hủy'
            });
            if (!result.isConfirmed) return;
        } else {
            if(!confirm('Đánh dấu yêu cầu này là Đã Giải Quyết?')) return;
        }
        
        try {
            const res = await fetch(`/support/resolve/${id}`, { method: 'POST' });
            const data = await res.json();
            if(data.success) {
                location.reload();
            } else {
                if (typeof Swal !== 'undefined') Swal.fire('Lỗi', data.msg, 'error');
                else alert('Lỗi: ' + data.msg);
            }
        } catch (e) {
            if (typeof Swal !== 'undefined') Swal.fire('Lỗi', 'Lỗi kết nối', 'error');
            else alert('Lỗi kết nối');
        }
    }

    async function deleteRequest(id) {
        if (typeof Swal !== 'undefined') {
            const result = await Swal.fire({
                title: 'Xóa yêu cầu?',
                text: 'Bạn có chắc chắn muốn xóa yêu cầu này? Hành động không thể hoàn tác.',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#DA1F3C',
                cancelButtonColor: '#6c757d',
                confirmButtonText: '<i class="fas fa-trash-alt me-1"></i> Xóa',
                cancelButtonText: 'Hủy'
            });
            if (!result.isConfirmed) return;
        } else {
            if(!confirm('Bạn có chắc chắn muốn xóa yêu cầu này?')) return;
        }
        
        try {
            const res = await fetch(`/support/delete/${id}`, { method: 'POST' });
            const data = await res.json();
            if(data.success) {
                location.reload();
            } else {
                if (typeof Swal !== 'undefined') Swal.fire('Lỗi', data.msg, 'error');
                else alert('Lỗi: ' + data.msg);
            }
        } catch (e) {
            if (typeof Swal !== 'undefined') Swal.fire('Lỗi', 'Lỗi kết nối', 'error');
            else alert('Lỗi kết nối');
        }
    }