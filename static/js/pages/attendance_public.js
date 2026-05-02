document.getElementById('lookupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const mssv = document.getElementById('mssvInput').value.trim();
        const btn = e.target.querySelector('button');
        const resultsPanel = document.getElementById('resultsPanel');
        const historyTbody = document.getElementById('historyTbody');
        
        if(!mssv) return;
        
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        btn.disabled = true;
        
        try {
            const res = await fetch('/public/api/lookup', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({mssv: mssv})
            });
            const data = await res.json();
            
            if(data.success) {
                // Đổ data thông tin
                document.getElementById('svName').innerText = data.student.ho_ten;
                document.getElementById('svId').innerText = data.student.mssv;
                document.getElementById('svClass').innerText = data.student.ten_lop;
                document.getElementById('svAvatar').innerText = data.student.ho_ten.charAt(0);
                
                // Đổ data bảng
                historyTbody.innerHTML = '';
                if(data.history.length > 0) {
                    data.history.forEach(item => {
                        let badgeClass = item.trang_thai === 'Co mat' ? 'status-ok' : 'status-warn';
                        let badgeIcon = item.trang_thai === 'Co mat' ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-exclamation-triangle"></i>';
                        let badgeText = item.trang_thai === 'Co mat' ? 'Có mặt' : item.trang_thai;
                        
                        historyTbody.innerHTML += `
                            <tr>
                                <td class="fw-medium text-white-50"><i class="far fa-clock me-2"></i>${item.thoi_gian}</td>
                                <td><i class="fas fa-layer-group text-white-50 me-2" style="font-size: 0.8rem"></i> ${item.ten_lop}</td>
                                <td class="text-end"><span class="status-badge ${badgeClass}">${badgeIcon} ${badgeText}</span></td>
                            </tr>
                        `;
                    });
                } else {
                    historyTbody.innerHTML = '<tr><td colspan="3" class="text-center py-4 text-muted">Bạn chưa có dữ liệu điểm danh nào.</td></tr>';
                }
                
                resultsPanel.classList.remove('d-none');
            } else {
                alert(data.msg);
                resultsPanel.classList.add('d-none');
            }
        } catch(err) {
            alert('Lỗi kết nối máy chủ');
        } finally {
            btn.innerHTML = 'Tra Cứu <i class="fas fa-arrow-right ms-2"></i>';
            btn.disabled = false;
        }
    });