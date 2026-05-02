function markResolved(alertId) {
        if(confirm('Xác nhận đã xử lý trường hợp này?')) {
            fetch(`/fraud/mark_resolved/${alertId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    location.reload();
                } else {
                    alert('Lỗi: ' + data.message);
                }
            })
            .catch(err => console.error(err));
        }
    }

    function deleteAlert(alertId) {
        if(confirm('Xóa vĩnh viễn log cảnh báo này?')) {
            fetch(`/fraud/delete/${alertId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('row-' + alertId).remove();
                } else {
                    alert('Lỗi: ' + data.message);
                }
            })
            .catch(err => console.error(err));
        }
    }