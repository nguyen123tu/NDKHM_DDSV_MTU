// Custom Modal logic
    function viewEvidence(url) {
        document.getElementById('evidenceImage').src = url;
        const modal = document.getElementById('evidenceModal');
        const content = document.getElementById('evidenceModalContent');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        void modal.offsetWidth; // trigger reflow
        
        modal.classList.replace('opacity-0', 'opacity-100');
        content.classList.replace('scale-95', 'scale-100');
    }

    function closeEvidenceModal() {
        const modal = document.getElementById('evidenceModal');
        const content = document.getElementById('evidenceModalContent');
        
        modal.classList.replace('opacity-100', 'opacity-0');
        content.classList.replace('scale-100', 'scale-95');
        
        setTimeout(() => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }, 300);
    }

    // Actions
    document.querySelectorAll('.btn-approve').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = e.currentTarget.getAttribute('data-id');
            if (confirm('Duyệt đơn xin phép này? Sinh viên sẽ nhận được thông báo qua hệ thống.')) {
                try {
                    const res = await fetch(`/attendance/approve-leave/${id}`, { method: 'POST' });
                    const data = await res.json();
                    if (data.success) location.reload();
                    else alert(data.message);
                } catch(e) { alert('Lỗi kết nối Server'); }
            }
        });
    });

    document.querySelectorAll('.btn-reject').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const id = e.currentTarget.getAttribute('data-id');
            if (confirm('Từ chối đơn xin phép này? Sinh viên sẽ vẫn bị tính vắng mặt.')) {
                try {
                    const res = await fetch(`/attendance/reject-leave/${id}`, { method: 'POST' });
                    const data = await res.json();
                    if (data.success) location.reload();
                    else alert(data.message);
                } catch(e) { alert('Lỗi kết nối Server'); }
            }
        });
    });