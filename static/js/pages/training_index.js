document.addEventListener('DOMContentLoaded', () => {
    const btnTrainAll = document.getElementById('btnTrainAll');
    const idlePanel = document.getElementById('idlePanel');
    const progressPanel = document.getElementById('progressPanel');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const statusText = document.getElementById('statusText');

    const dfAntiSpoof = document.getElementById('dfAntiSpoof');
    if(dfAntiSpoof) dfAntiSpoof.addEventListener('change', () => {
        document.getElementById('dfAntiSpoofLabel').textContent = dfAntiSpoof.checked ? 'BẬT' : 'TẮT';
    });

    btnTrainAll.addEventListener('click', async () => {
        if(!confirm('Chạy lại Training AI toàn bộ?\n\nDừng Camera trước khi chạy.')) return;
        btnTrainAll.disabled = true;
        if (typeof showProgress === 'function') {
            showProgress();
        } else {
            idlePanel.style.display = 'none';
            progressPanel.style.display = 'block';
        }
        const t0 = Date.now();
        const timer = setInterval(() => {
            const s = Math.floor((Date.now()-t0)/1000);
            const el = document.getElementById('elapsedTime');
            if(el) el.textContent = s>=60 ? `${Math.floor(s/60)}m ${s%60}s` : `${s}s`;
        }, 1000);
        try {
            await fetch('/training/start', {method:'POST'});
            const es = new EventSource('/training/progress');
            es.onmessage = function(e) {
                const d = JSON.parse(e.data);
                const pct = Math.round(d.progress*100);
                progressBar.style.width = pct+'%';
                progressText.innerText = pct+'%';
                if(d.status==='training') {
                    statusText.innerText = 'Đang trích xuất Vector...';
                    if(d.current_student) document.getElementById('currentStudentLabel').textContent = d.current_student;
                    if(d.detail) document.getElementById('detailLabel').textContent = d.detail;
                }
                if(d.status==='done'||d.status==='error') {
                    es.close(); clearInterval(timer);
                    progressBar.classList.remove('progress-bar-animated');
                    if(d.status==='done') {
                        statusText.innerText = 'Hoàn tất!';
                        document.getElementById('currentStudentLabel').textContent = '✅ Xong!';
                        setTimeout(() => location.reload(), 2000);
                    } else {
                        statusText.innerText = 'Có lỗi!';
                        btnTrainAll.disabled = false;
                        if (typeof hideProgress === 'function') hideProgress();
                    }
                }
            };
        } catch(err) { 
            alert('Lỗi Server'); 
            clearInterval(timer); 
            btnTrainAll.disabled=false; 
            if (typeof hideProgress === 'function') hideProgress();
        }
    });

    document.querySelectorAll('.btn-train-single:not([disabled])').forEach(btn => {
        btn.addEventListener('click', async e => {
            const mssv = e.currentTarget.getAttribute('data-mssv');
            e.currentTarget.disabled = true;
            e.currentTarget.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ...';
            try {
                const res = await fetch(`/training/student/${mssv}`, {method:'POST'});
                const d = await res.json();
                if(d.success) { alert('Thành công!'); location.reload(); }
                else { alert('Lỗi: '+d.msg); e.currentTarget.disabled=false; e.currentTarget.innerHTML='<i class="fas fa-brain me-1"></i>Train'; }
            } catch(err) { alert('Lỗi'); e.currentTarget.disabled=false; }
        });
    });
});

async function switchEngine(engine) {
    const labels = {'insightface':'InsightFace','yolo_resnet':'YOLOv11+ResNet50','deepface':'DeepFace'};
    if(!confirm(`Chuyển sang ${labels[engine]}?\n\nCần TRAIN LẠI nếu chưa có file não bộ.`)) return;
    let payload = {engine};
    if(engine==='deepface') {
        payload.deepface_model = document.getElementById('dfModel').value;
        payload.deepface_detector = document.getElementById('dfDetector').value;
        payload.deepface_anti_spoofing = document.getElementById('dfAntiSpoof').checked;
        payload.deepface_analysis = Array.from(document.querySelectorAll('.df-analysis:checked')).map(c=>c.value).join(',');
    }
    try {
        const res = await fetch('/training/switch-engine',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
        const d = await res.json();
        if(d.success) setTimeout(()=>location.reload(),500);
        else alert('Lỗi: '+d.msg);
    } catch(err) { alert('Lỗi Server'); }
}

async function applyDeepFaceConfig() {
    const btn = document.getElementById('btnApplyDfConfig');
    btn.disabled=true; btn.innerHTML='<i class="fas fa-spinner fa-spin me-1"></i>...';
    const payload = {engine:'deepface',deepface_model:document.getElementById('dfModel').value,deepface_detector:document.getElementById('dfDetector').value,deepface_anti_spoofing:document.getElementById('dfAntiSpoof').checked,deepface_analysis:Array.from(document.querySelectorAll('.df-analysis:checked')).map(c=>c.value).join(',')};
    try {
        const res = await fetch('/training/switch-engine',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
        const d = await res.json();
        if(d.success) { btn.innerHTML='<i class="fas fa-check me-1"></i>Đã lưu!'; btn.style.background='var(--success)'; setTimeout(()=>location.reload(),1000); }
        else { alert('Lỗi: '+d.msg); btn.disabled=false; btn.innerHTML='<i class="fas fa-save me-1"></i>Lưu'; }
    } catch(err) { alert('Lỗi'); btn.disabled=false; btn.innerHTML='<i class="fas fa-save me-1"></i>Lưu'; }
}