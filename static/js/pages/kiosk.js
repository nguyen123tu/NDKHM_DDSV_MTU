// Clock
function updateClock() {
    document.getElementById('clock').innerText = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
setInterval(updateClock, 1000); updateClock();

// Camera
const video = document.getElementById('webcam'), rtspImg = document.getElementById('rtspVideo'), canvas = document.getElementById('canvas-capture'), ctx = canvas.getContext('2d');
const selectCamSource = document.getElementById('selectCamSource');
let currentStream = null;
let rtspUrl = localStorage.getItem('kiosk_rtsp_url') || "rtsp://admin:L2F0C994@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0";

async function setupCamera() {
    video.style.display = 'block';
    rtspImg.style.display = 'none';
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
        currentStream = stream;
        video.srcObject = stream;
    } catch (err) {
        console.error("Cam Error:", err);
        if (err.name === 'NotAllowedError') {
            alert("Cần cấp quyền Camera cho trình duyệt!");
        } else {
            console.log("Thử lại với cấu hình Camera mặc định...");
            try {
                const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                currentStream = fallbackStream;
                video.srcObject = fallbackStream;
            } catch (fallbackErr) {
                console.error("Fallback Cam Error:", fallbackErr);
            }
        }
    }
}

function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(t => t.stop());
        currentStream = null;
    }
}

function initCamSelection() {
    if (selectCamSource) {
        const savedSource = localStorage.getItem('kiosk_cam_source');
        if (savedSource) {
            selectCamSource.value = savedSource;
        }

        selectCamSource.addEventListener('change', (e) => {
            localStorage.setItem('kiosk_cam_source', e.target.value);
            if (e.target.value === 'rtsp') {
                stopCamera();
                let userRtsp = prompt("Nhập Link RTSP Camera IMOU:", rtspUrl);
                if (userRtsp) {
                    rtspUrl = userRtsp;
                    localStorage.setItem('kiosk_rtsp_url', rtspUrl);
                    video.style.display = 'none';
                    rtspImg.style.display = 'block';
                    rtspImg.src = '/public/api/stream_kiosk?url=' + encodeURIComponent(rtspUrl);
                } else {
                    selectCamSource.value = 'webcam';
                    localStorage.setItem('kiosk_cam_source', 'webcam');
                    setupCamera();
                }
            } else {
                rtspImg.src = '';
                setupCamera();
            }
        });

        if (selectCamSource.value === 'rtsp') {
            video.style.display = 'none';
            rtspImg.style.display = 'block';
            rtspImg.src = '/public/api/stream_kiosk?url=' + encodeURIComponent(rtspUrl);
        } else {
            setupCamera();
        }
    } else {
        setupCamera();
    }
}

let isProcessing = false, lastMssv = null, lastTime = 0;
async function captureAndRecognize() {
    const isRtsp = selectCamSource && selectCamSource.value === 'rtsp';
    const srcElem = isRtsp ? rtspImg : video;

    if (isProcessing) return;
    if (!isRtsp && video.videoWidth === 0) return;
    if (isRtsp && rtspImg.naturalWidth === 0) return;

    const lopSelect = document.getElementById('kiosk-lop-id');
    const lopId = lopSelect ? lopSelect.value : '';
    const startTimeInput = document.getElementById('kiosk-start-time');
    const startTime = startTimeInput ? startTimeInput.value : '07:00';

    let reqBody = {};
    if (lopId) reqBody.lop_id = parseInt(lopId);
    reqBody.start_time = startTime;

    if (isRtsp) {
        reqBody.rtsp_url = rtspUrl;
    } else {
        const MAX_WIDTH = 1280;
        let nw = video.videoWidth;
        let nh = video.videoHeight;

        if (nw > MAX_WIDTH) {
            nh = Math.floor(nh * (MAX_WIDTH / nw));
            nw = MAX_WIDTH;
        }

        canvas.width = nw;
        canvas.height = nh;

        try {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        } catch (e) { return; }

        reqBody.image = canvas.toDataURL('image/jpeg', 0.6);
    }

    isProcessing = true;
    try {
        const res = await fetch('/public/api/recognize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(reqBody) });
        if (!res.ok) throw new Error("Server error");
        const d = await res.json();
        if (d.success) {
            const now = Date.now();
            if (d.student.mssv !== lastMssv || (now - lastTime > 10000)) {
                showResult(d); lastMssv = d.student.mssv; lastTime = now;
            }
        } else {
            if (d.msg && d.msg !== "Không có ảnh" && d.msg !== "Không phát hiện khuôn mặt. Hãy nhìn thẳng vào camera.") {
                showError(d.msg);
            }
        }
    } catch (e) { console.error("API:", e) }
    finally { setTimeout(() => { isProcessing = false }, 2000) }
}

// ===== Unlock Audio =====
const btnUnlockAudio = document.getElementById('btnUnlockAudio');
const ttsAudio = document.getElementById('ttsAudio');
if (btnUnlockAudio) {
    btnUnlockAudio.addEventListener('click', () => {
        ttsAudio.play().catch(e => { }); // Play empty to unlock
        btnUnlockAudio.classList.remove('btn-outline-info');
        btnUnlockAudio.classList.add('btn-info');
        btnUnlockAudio.innerHTML = '<i class="fas fa-volume-up"></i> Bật';
    });
}

function showResult(data) {
    const p = document.getElementById('result-panel'), s = data.student, a = data.attendance;
    const status = document.getElementById('res-status');

    document.getElementById('res-name').innerText = s.ho_ten;
    document.getElementById('res-mssv').innerText = `MSSV: ${s.mssv}`;
    document.getElementById('res-avatar').src = s.avatar ? `/${s.avatar}` : '/static/img/logo_MTU.jpg';
    document.getElementById('res-msg').innerText = a ? (a.msg || "Điểm danh hoàn tất") : "Nhận diện thành công";
    
    const now = new Date();
    const timeValEl = document.getElementById('res-time-val');
    if (timeValEl) timeValEl.innerText = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    status.className = "res-badge res-badge-ok";
    status.innerHTML = '<i class="fas fa-shield-check"></i> Access Granted';

    // TTS Audio
    if (ttsAudio) {
        const text = `Xin chào ${s.ho_ten}, điểm danh thành công!`;
        ttsAudio.src = `/chatbot/tts?text=${encodeURIComponent(text)}`;
        ttsAudio.play().catch(e => {
            console.log('Audio autoplay bị chặn:', e);
            if (btnUnlockAudio) btnUnlockAudio.classList.add('btn-danger');
        });
    }

    p.style.display = 'block';
    addLog(s);
    setTimeout(() => { p.style.display = 'none' }, 5000);
}

function showError(msg) {
    const p = document.getElementById('result-panel');
    const status = document.getElementById('res-status');

    document.getElementById('res-name').innerText = "Cảnh Báo";
    document.getElementById('res-mssv').innerText = "Vui lòng thử lại";
    document.getElementById('res-avatar').src = '/static/img/logo_MTU.jpg';
    document.getElementById('res-msg').innerText = msg;

    const now = new Date();
    const timeValEl = document.getElementById('res-time-val');
    if (timeValEl) timeValEl.innerText = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    status.className = "res-badge res-badge-err";
    status.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Access Denied';

    if (ttsAudio) {
        ttsAudio.src = `/chatbot/tts?text=${encodeURIComponent("Nhận diện thất bại")}`;
        ttsAudio.play().catch(e => { });
    }

    p.style.display = 'block';
    setTimeout(() => { p.style.display = 'none'; }, 4000);
}

function addLog(s) {
    const c = document.getElementById('log-container');
    const t = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    const item = document.createElement('div');
    item.className = 'log-item';
    item.innerHTML = `<span class="log-time">${t}</span><div class="flex-grow-1"><div class="log-name">${s.ho_ten}</div><div class="log-mssv">${s.mssv}</div></div><span class="log-check"><i class="fas fa-check-circle"></i></span>`;
    if (c.children[0] && c.children[0].classList.contains('text-center')) c.innerHTML = '';
    c.prepend(item);
    if (c.children.length > 15) c.removeChild(c.lastChild);
    const sc = document.getElementById('stat-count');
    sc.innerText = parseInt(sc.innerText) + 1;
}

initCamSelection();
setInterval(captureAndRecognize, 2000);