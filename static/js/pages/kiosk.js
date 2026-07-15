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
            Swal.fire({ icon: 'error', title: 'Từ chối quyền Camera', text: 'Vào Cài đặt trình duyệt → Quyền riêng tư → Cho phép Camera.' });
        } else if (err.name === 'NotFoundError') {
            Swal.fire({ icon: 'error', title: 'Không tìm thấy Camera', text: 'Kiểm tra xem thiết bị có webcam không hoặc camera có đang bị ứng dụng khác chiếm?' });
        } else if (err.name === 'NotReadableError') {
            Swal.fire({ icon: 'warning', title: 'Camera đang bị chiếm dụng', text: 'Đóng các ứng dụng đang dùng camera (Zoom, Teams...) rồi thử lại.' });
        } else {
            console.log("Thử lại với cấu hình Camera mặc định...");
            try {
                const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                currentStream = fallbackStream;
                video.srcObject = fallbackStream;
            } catch (fallbackErr) {
                console.error("Fallback Cam Error:", fallbackErr);
                Swal.fire({ icon: 'error', title: 'Lỗi khởi tạo Camera', text: fallbackErr.message + '\n\nThử mở bằng Chrome hoặc Edge.' });
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
let isProcessing = false, lastMssv = null, lastTime = 0;
async function captureAndRecognize() {
    const source = localStorage.getItem('kiosk_cam_source') || 'webcam';
    const isRtsp = source.startsWith('rtsp');
    const srcElem = isRtsp ? rtspImg : video;

    if (isProcessing) return;
    if (!isRtsp && video.videoWidth === 0) return;
    if (isRtsp && rtspImg.naturalWidth === 0) return;

    const lopId = localStorage.getItem('kiosk_lop_id');
    const startTime = localStorage.getItem('kiosk_start_time') || 'auto';

    if (!lopId) return;

    let reqBody = { lop_id: parseInt(lopId), start_time: startTime };

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
        const res = await fetch('/public/api/recognize', { method: 'POST', headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '1' }, body: JSON.stringify(reqBody) });
        if (!res.ok) throw new Error("Server error");
        const d = await res.json();
        if (d.success) {
            const now = Date.now();
            if (d.student.mssv !== lastMssv || (now - lastTime > 10000)) {
                showResult(d); lastMssv = d.student.mssv; lastTime = now;
            }
        } else {
            if (d.msg && d.msg !== "Không có ảnh" && d.msg !== "Không phát hiện khuôn mặt. Hãy nhìn thẳng vào camera.") {
                showError(d.msg, d.is_unknown);
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

function showError(msg, isUnknown = false) {
    const p = document.getElementById('result-panel');
    const status = document.getElementById('res-status');

    document.getElementById('res-name').innerText = isUnknown ? "Người Lạ" : "Cảnh Báo";
    document.getElementById('res-mssv').innerText = isUnknown ? "Chưa đăng ký khuôn mặt" : "Vui lòng thử lại";
    document.getElementById('res-avatar').src = '/static/img/logo_MTU.jpg';
    document.getElementById('res-msg').innerText = msg;

    const now = new Date();
    const timeValEl = document.getElementById('res-time-val');
    if (timeValEl) timeValEl.innerText = now.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    status.className = "res-badge res-badge-err";
    status.innerHTML = isUnknown ? '<i class="fas fa-user-secret"></i> Unknown User' : '<i class="fas fa-exclamation-triangle"></i> Access Denied';

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

// ===== Pre-Livestream Setup Flow =====
let processInterval = null;
let previewStream = null;

const setupScreen = document.getElementById('setupScreen');
const btnGoLive = document.getElementById('btnGoLive');
const btnShowConfig = document.getElementById('btnShowConfig');

const setupCamSource = document.getElementById('setupCamSource');
const setupLopId = document.getElementById('setupLopId');
const setupStartTime = document.getElementById('setupStartTime');

const previewWebcam = document.getElementById('previewWebcam');
const previewRtsp = document.getElementById('previewRtsp');
const previewPlaceholder = document.getElementById('previewPlaceholder');
const previewStatus = document.getElementById('previewStatus');
const previewLoading = document.getElementById('previewLoading');
const previewIcon = document.getElementById('previewIcon');
const previewText = document.getElementById('previewText');

function stopPreview() {
    if (previewStream) {
        previewStream.getTracks().forEach(t => t.stop());
        previewStream = null;
    }
    if (previewWebcam) {
        previewWebcam.style.display = 'none';
        previewWebcam.srcObject = null;
    }
    if (previewRtsp) {
        previewRtsp.style.display = 'none';
        previewRtsp.src = '';
    }
}

function startPreview() {
    stopPreview();
    if (!previewPlaceholder) return;
    previewPlaceholder.classList.remove('d-none');
    previewIcon.classList.add('d-none');
    previewLoading.classList.remove('d-none');
    previewText.innerText = 'Đang kết nối...';
    previewStatus.className = 'badge bg-warning text-dark';
    previewStatus.innerText = 'Đang tải...';

    const source = setupCamSource ? setupCamSource.value : 'webcam';
    if (source === 'webcam') {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            previewLoading.classList.add('d-none');
            previewIcon.classList.remove('d-none');
            previewIcon.className = 'fas fa-shield-alt mb-3 text-warning';
            previewText.innerHTML = '<span class="text-warning">Trình duyệt chặn Camera (Cần dùng HTTPS/Localhost)</span>';
            previewStatus.className = 'badge bg-danger';
            previewStatus.innerText = 'Lỗi Bảo Mật';
            return;
        }
        navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false })
            .then(stream => {
                previewStream = stream;
                previewWebcam.srcObject = stream;
                previewWebcam.style.display = 'block';
                previewPlaceholder.classList.add('d-none');
                previewStatus.className = 'badge bg-success';
                previewStatus.innerText = 'Sẵn sàng (Webcam)';
            })
            .catch(err => {
                previewLoading.classList.add('d-none');
                previewIcon.classList.remove('d-none');
                previewIcon.className = 'fas fa-exclamation-triangle mb-3 text-danger';
                previewText.innerHTML = '<span class="text-danger">Không thể truy cập Webcam</span>';
                previewStatus.className = 'badge bg-danger';
                previewStatus.innerText = 'Lỗi Webcam';
            });
    } else if (source.startsWith('rtsp')) {
        let currentUrl = rtspUrl;
        if (source === 'rtsp_lan') currentUrl = 'rtsp://admin:L2F0C994@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0';
        else if (source === 'rtsp_wan') currentUrl = 'rtsp://admin:L2F0C994@192.168.1.80:554/cam/realmonitor?channel=1&subtype=0';
        
        previewRtsp.src = '/public/api/stream_kiosk?url=' + encodeURIComponent(currentUrl);
        previewRtsp.style.display = 'block';
        previewRtsp.onload = () => {
            previewPlaceholder.classList.add('d-none');
            previewStatus.className = 'badge bg-success';
            previewStatus.innerText = 'Sẵn sàng (RTSP)';
        };
        previewRtsp.onerror = () => {
            previewRtsp.style.display = 'none';
            previewLoading.classList.add('d-none');
            previewIcon.classList.remove('d-none');
            previewIcon.className = 'fas fa-network-wired mb-3 text-danger';
            previewText.innerHTML = '<span class="text-danger">Không thể kết nối luồng RTSP</span>';
            previewStatus.className = 'badge bg-danger';
            previewStatus.innerText = 'Lỗi Mạng';
        };
    }
}

if (setupCamSource) {
    const savedSource = localStorage.getItem('kiosk_cam_source');
    if (savedSource) setupCamSource.value = savedSource;
    
    setupCamSource.addEventListener('change', (e) => {
        localStorage.setItem('kiosk_cam_source', e.target.value);
        if (e.target.value === 'rtsp_custom') {
            let userRtsp = prompt("Vui lòng nhập Link RTSP của Camera IMOU:", rtspUrl);
            if (userRtsp) {
                rtspUrl = userRtsp;
                localStorage.setItem('kiosk_rtsp_url', rtspUrl);
            } else {
                setupCamSource.value = 'webcam';
                localStorage.setItem('kiosk_cam_source', 'webcam');
            }
        }
        startPreview();
    });
}

if (setupLopId) {
    const savedLopId = localStorage.getItem('kiosk_lop_id');
    if (savedLopId) setupLopId.value = savedLopId;
}

if (setupStartTime) {
    const savedTime = localStorage.getItem('kiosk_start_time') || 'auto';
    if (savedTime) setupStartTime.value = savedTime;
}

if (setupScreen && setupScreen.style.display !== 'none') {
    startPreview();
}

if (btnGoLive) {
    btnGoLive.addEventListener('click', () => {
        if (setupLopId && !setupLopId.value) {
            alert('Vui lòng chọn lớp điểm danh!');
            return;
        }
        
        if (setupLopId) localStorage.setItem('kiosk_lop_id', setupLopId.value);
        if (setupStartTime) localStorage.setItem('kiosk_start_time', setupStartTime.value);
        
        stopPreview();
        
        setupScreen.classList.remove('d-flex');
        setupScreen.style.display = 'none';
        
        // Bắt đầu Camera chính
        if (setupCamSource && setupCamSource.value.startsWith('rtsp')) {
            video.style.display = 'none';
            rtspImg.style.display = 'block';
            let currentUrl = rtspUrl;
            if (setupCamSource.value === 'rtsp_lan') currentUrl = 'rtsp://admin:L2F0C994@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0';
            else if (setupCamSource.value === 'rtsp_wan') currentUrl = 'rtsp://admin:L2F0C994@192.168.1.80:554/cam/realmonitor?channel=1&subtype=0';
            
            rtspUrl = currentUrl; // Update global for captureAndRecognize
            rtspImg.src = '/public/api/stream_kiosk?url=' + encodeURIComponent(currentUrl);
        } else {
            rtspImg.src = '';
            setupCamera();
        }
        
        if (!processInterval) {
            processInterval = setInterval(captureAndRecognize, 1200);
        }
        
        if (ttsAudio) ttsAudio.play().catch(e => {}); 
    });
}

if (btnShowConfig) {
    btnShowConfig.addEventListener('click', () => {
        if (processInterval) {
            clearInterval(processInterval);
            processInterval = null;
        }
        
        stopCamera();
        if (rtspImg) {
            rtspImg.src = '';
            rtspImg.style.display = 'none';
        }
        
        setupScreen.style.display = 'flex';
        setupScreen.classList.add('d-flex');
        startPreview();
    });
}