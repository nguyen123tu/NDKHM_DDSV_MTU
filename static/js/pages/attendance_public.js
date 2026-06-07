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
                const sv = data.student;
                document.getElementById('svName').innerText = sv.ho_ten;
                document.getElementById('svId').innerText = sv.mssv;
                document.getElementById('spMssv').value = sv.mssv;
                document.getElementById('svClass').innerText = sv.ten_lop;
                document.getElementById('svEmail').innerText = sv.email;
                document.getElementById('svDob').innerText = sv.ngay_sinh;
                document.getElementById('svGender').innerText = sv.gioi_tinh;
                
                // Cập nhật Avatar
                if(sv.avatar) {
                    document.getElementById('svAvatarImg').src = '/' + sv.avatar;
                    document.getElementById('svAvatarImg').classList.remove('d-none');
                    document.getElementById('svAvatar').classList.add('d-none');
                } else {
                    document.getElementById('svAvatarImg').classList.add('d-none');
                    document.getElementById('svAvatar').classList.remove('d-none');
                    document.getElementById('svAvatar').innerText = sv.ho_ten.charAt(0);
                }
                
                // Đổ data Thống kê
                if(data.stats) {
                    document.getElementById('statPresent').innerText = data.stats.present;
                }
                
                // Đổ data Lưới ảnh AI
                const faceGrid = document.getElementById('faceGrid');
                faceGrid.innerHTML = '';
                document.getElementById('faceCount').innerText = `${data.face_data.length} ảnh`;
                
                if(data.face_data && data.face_data.length > 0) {
                    // Show up to 6 images
                    const displayImages = data.face_data.slice(0, 6);
                    displayImages.forEach(imgPath => {
                        faceGrid.innerHTML += `<img src="/${imgPath}" alt="Face Data">`;
                    });
                    
                    // Fill remaining grid spaces with empty placeholders
                    const remaining = 6 - displayImages.length;
                    for(let i=0; i<remaining; i++) {
                        faceGrid.innerHTML += `<div class="face-empty"><i class="fas fa-user-shield"></i></div>`;
                    }
                } else {
                    for(let i=0; i<6; i++) {
                        faceGrid.innerHTML += `<div class="face-empty"><i class="fas fa-user-shield"></i></div>`;
                    }
                    document.getElementById('svAiStatus').className = 'badge bg-warning bg-opacity-25 text-warning border border-warning border-opacity-50 px-3 py-2 rounded-pill mb-4';
                    document.getElementById('svAiStatus').innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i> Chưa có dữ liệu khuôn mặt';
                }
                
                // Đổ data bảng lịch sử
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
    // Xử lý gửi Yêu cầu hỗ trợ
    const supportForm = document.getElementById('supportForm');
    if (supportForm) {
        supportForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btnSubmitSupport');
            const mssv = document.getElementById('spMssv').value;
            const tieu_de = document.getElementById('spTitle').value;
            const noi_dung = document.getElementById('spContent').value;
            
            if (!mssv || !tieu_de || !noi_dung) return;
            
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang gửi...';
            btn.disabled = true;
            
            try {
                const res = await fetch('/public/api/support', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({mssv, tieu_de, noi_dung})
                });
                const data = await res.json();
                
                if (data.success) {
                    alert('Gửi yêu cầu thành công! Quản trị viên sẽ sớm xử lý.');
                    supportForm.reset();
                    document.getElementById('spMssv').value = mssv; // retain mssv
                    
                    // Close modal using bootstrap API
                    const modalEl = document.getElementById('supportModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    if(modal) modal.hide();
                } else {
                    alert(data.msg || 'Đã có lỗi xảy ra');
                }
            } catch (err) {
                alert('Lỗi kết nối máy chủ');
            } finally {
                btn.innerHTML = 'Gửi Yêu Cầu <i class="fas fa-paper-plane ms-2"></i>';
                btn.disabled = false;
            }
        });
    }
