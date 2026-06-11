function markResolved(alertId) {
    Swal.fire({
        title: 'Xác nhận',
        text: 'Đánh dấu đã xử lý trường hợp này?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Đồng ý',
        cancelButtonText: 'Hủy'
    }).then((result) => {
        if(result.isConfirmed) {
            fetch(`/fraud/mark_resolved/${alertId}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.success) location.reload();
                else Swal.fire('Lỗi', data.message, 'error');
            });
        }
    });
}

function deleteAlert(alertId) {
    Swal.fire({
        title: 'Xóa bản ghi?',
        text: 'Xóa vĩnh viễn log cảnh báo này?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Xóa',
        cancelButtonText: 'Hủy'
    }).then((result) => {
        if(result.isConfirmed) {
            fetch(`/fraud/delete/${alertId}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.success) document.getElementById('row-' + alertId).remove();
                else Swal.fire('Lỗi', data.message, 'error');
            });
        }
    });
}

function cancelAttendance(alertId) {
    Swal.fire({
        title: 'Hủy Điểm Danh?',
        text: 'Xác nhận xóa toàn bộ dữ liệu điểm danh của sinh viên này trong ngày hôm nay?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f6c23e',
        confirmButtonText: 'Xác nhận Hủy',
        cancelButtonText: 'Đóng'
    }).then((result) => {
        if(result.isConfirmed) {
            fetch(`/fraud/cancel_attendance/${alertId}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    Swal.fire('Thành công', data.message, 'success').then(() => location.reload());
                } else Swal.fire('Lỗi', data.message, 'error');
            });
        }
    });
}

function lockAccount(alertId, svName) {
    Swal.fire({
        title: 'Khóa / Mở Tài Khoản?',
        html: `Bạn sắp thay đổi trạng thái khóa của sinh viên <b>${svName}</b>.<br><br>Gõ chữ <b>XAC NHAN</b> để tiếp tục:`,
        input: 'text',
        icon: 'error',
        showCancelButton: true,
        confirmButtonColor: '#e74a3b',
        confirmButtonText: 'Thực thi',
        cancelButtonText: 'Hủy',
        preConfirm: (inputValue) => {
            if (inputValue !== 'XAC NHAN') {
                Swal.showValidationMessage('Bạn phải gõ chính xác XAC NHAN');
            }
        }
    }).then((result) => {
        if(result.isConfirmed) {
            fetch(`/fraud/lock_account/${alertId}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    Swal.fire('Thành công', data.message, 'success').then(() => location.reload());
                } else Swal.fire('Lỗi', data.message, 'error');
            });
        }
    });
}