document.addEventListener("DOMContentLoaded", () => {
        let lastStudentIdForEdit = null;

        // === Thêm sinh viên mới ===
        document.getElementById('btnSaveStudent').addEventListener('click', async () => {
            const mssv = document.getElementById('addMssv').value.trim();
            const hoTen = document.getElementById('addHoTen').value.trim();
            const lopId = document.getElementById('addLopId').value;

            if(!mssv || !hoTen || !lopId) {
                alert('Vui lòng nhập đầy đủ Mã sinh viên, Họ và tên và Lớp học!');
                return;
            }

            const btnSave = document.getElementById('btnSaveStudent');
            const originalText = btnSave.innerHTML;
            btnSave.disabled = true;
            btnSave.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Đang lưu...';

            try {
                const res = await fetch('/students/api/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mssv: mssv, ho_ten: hoTen, lop_id: lopId, images: [] })
                });
                const data = await res.json();
                if(data.success) {
                    if (document.getElementById('chkGoCapture').checked) {
                        window.location.href = `/training/capture/${mssv}`;
                    } else {
                        alert('Thêm sinh viên thành công!');
                        window.location.reload();
                    }
                } else {
                    alert('Lỗi: ' + data.msg);
                }
            } catch(e) {
                console.error(e);
                alert('Lỗi kết nối tới Server!');
            } finally {
                btnSave.disabled = false;
                btnSave.innerHTML = originalText;
            }
        });

        // === Quản lý ảnh sinh viên ===
        document.querySelectorAll('.btn-manage-images').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const mssv = e.currentTarget.getAttribute('data-mssv');
                const name = e.currentTarget.getAttribute('data-name');
                const lop = e.currentTarget.getAttribute('data-lop');

                // Find edit link for student ID
                const row = e.currentTarget.closest('.student-row');
                const editLink = row.querySelector('.act-btn-edit');
                if (editLink) {
                    const href = editLink.getAttribute('href');
                    lastStudentIdForEdit = href.split('/').filter(Boolean).slice(-2, -1)[0];
                }

                document.getElementById('imgMgrName').textContent = name;
                document.getElementById('imgMgrMssv').textContent = mssv;
                document.getElementById('imgMgrLop').textContent = lop;

                const gallery = document.getElementById('imgMgrGallery');
                gallery.innerHTML = '<div class="col-12 text-center text-muted py-5"><i class="fas fa-spinner fa-spin fs-2 mb-2"></i><p>Đang tải ảnh...</p></div>';

                new bootstrap.Modal(document.getElementById('imageManagerModal')).show();

                try {
                    const res = await fetch(`/students/api/images/${mssv}`);
                    const images = await res.json();

                    if (images.length === 0) {
                        gallery.innerHTML = '<div class="col-12 text-center py-5"><div style="font-size:3rem;opacity:.3;margin-bottom:12px">📷</div><h6 class="fw-bold">Chưa có ảnh</h6><p class="small text-muted">Vào Training → Chụp ảnh để thu thập khuôn mặt</p></div>';
                        return;
                    }

                    gallery.innerHTML = '';
                    images.forEach(img => {
                        gallery.innerHTML += `
                            <div class="col-4 col-md-3">
                                <div style="background:#FAFAFF;border:2px solid #E8E6F0;border-radius:12px;padding:6px;text-align:center;">
                                    <img src="/database/${img}" style="height:100px;width:100%;object-fit:cover;border-radius:8px;">
                                    <span class="small text-muted d-block mt-1" style="font-size:.7rem">${img.split('/').pop()}</span>
                                </div>
                            </div>
                        `;
                    });
                } catch(e) {
                    console.error(e);
                    gallery.innerHTML = '<div class="col-12 text-center text-danger py-4">Lỗi không thể tải ảnh!</div>';
                }
            });
        });

        document.getElementById('btnEditInfoLink').addEventListener('click', () => {
            if (lastStudentIdForEdit) {
                window.location.href = `/students/${lastStudentIdForEdit}/edit`;
            }
        });

        // === Xóa sinh viên với SweetAlert2 ===
        document.querySelectorAll('.form-delete-student').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const studentName = this.getAttribute('data-name');
                
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        title: 'Xóa sinh viên?',
                        html: `Bạn có chắc chắn muốn xóa sinh viên <strong style="color:var(--primary)">${studentName}</strong>?<br><span class="text-danger small mt-2 d-block">Hành động này không thể hoàn tác và sẽ xóa tất cả dữ liệu liên quan.</span>`,
                        icon: 'warning',
                        showCancelButton: true,
                        confirmButtonColor: '#DA1F3C',
                        cancelButtonColor: '#CBD5E1',
                        confirmButtonText: '<i class="fas fa-trash-alt me-1"></i> Đồng ý xóa',
                        cancelButtonText: 'Hủy',
                        customClass: {
                            cancelButton: 'text-dark'
                        }
                    }).then((result) => {
                        if (result.isConfirmed) {
                            this.submit();
                        }
                    });
                } else {
                    if (confirm(`Xóa sinh viên ${studentName}?`)) {
                        this.submit();
                    }
                }
            });
        });
    });