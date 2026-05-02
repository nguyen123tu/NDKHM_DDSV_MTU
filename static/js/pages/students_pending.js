function viewAllImages(mssv) {
    const modalElement = document.getElementById('imageModal');
    const modal = new bootstrap.Modal(modalElement);
    document.getElementById('modalMssv').innerText = mssv;
    const grid = document.getElementById('imageGrid');
    
    grid.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="text-muted small mt-2">Đang tải bộ mẫu dữ liệu...</p>
        </div>`;
    
    modal.show();
    
    if (!mssv) return;
    
    fetch(`/api/mobile/face-gallery?mssv=${encodeURIComponent(mssv)}`, {
        headers: {
            'Authorization': 'Bearer ' + (localStorage.getItem('token') || '')
        }
    })
    .then(r => r.json())
    .then(res => {
        if (res.success && res.data.length > 0) {
            grid.innerHTML = '';
            res.data.forEach(path => {
                const col = document.createElement('div');
                col.className = 'col-6 col-md-3';
                col.innerHTML = `
                    <div class="card border-0 shadow-sm overflow-hidden h-100">
                        <img src="/database/${path}" class="img-fluid" alt="Face sample">
                    </div>`;
                grid.appendChild(col);
            });
        } else {
            grid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fas fa-image fs-1 text-muted opacity-25"></i>
                    <p class="text-muted mt-2">Không tìm thấy ảnh thực tế trong folder!</p>
                </div>`;
        }
    })
    .catch(err => {
        grid.innerHTML = `<div class="col-12 text-center text-danger py-5">Lỗi kết nối API: ${err}</div>`;
    });
}