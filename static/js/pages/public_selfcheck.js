// ========== Clock ==========
function updateClock() {
    const now = new Date();
    const days = ['Chủ Nhật','Thứ Hai','Thứ Ba','Thứ Tư','Thứ Năm','Thứ Sáu','Thứ Bảy'];
    const pad = n => (n < 10 ? '0' : '') + n;
    document.getElementById('realtimeClock').innerText =
        `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())} — ${days[now.getDay()]}, ${now.getDate()}/${now.getMonth()+1}/${now.getFullYear()}`;
}
setInterval(updateClock, 1000);
updateClock();

// ========== Main Logic ==========
document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('webcamVideo');
    const canvas = document.getElementById('captureCanvas');
    const scanBox = document.getElementById('scanBox');
    const scanNameTag = document.getElementById('scanNameTag');
    const logList = document.getElementById('logList');

    let isProcessing = false;
    let logCount = 0;
    let lastMSSV = '';
    let lastTime = 0;

    const rtspImg = document.getElementById('rtspVideo');
    const selectCamSource = document.getElementById('selectCamSource');
    let currentStream = null;
    let rtspUrl = localStorage.getItem('kiosk_rtsp_url') || "rtsp://admin:L2F0C994@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0";

    function startWebcam() {
        video.style.display = 'block';
        rtspImg.style.display = 'none';
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
        .then(stream => {
            currentStream = stream;
            video.srcObject = stream;
            document.getElementById('cameraBadge').style.display = 'flex';
            document.getElementById('camStatusText').innerHTML = '<i class="fas fa-check-circle text-success me-1"></i> Sẵn sàng';
        })
        .catch((err) => {
            console.error('Camera Error:', err);
            let msg = '<i class="fas fa-times-circle text-danger me-1"></i> Không truy cập được camera';
            if (err.name === 'NotFoundError') msg = '<i class="fas fa-times-circle text-danger me-1"></i> Không tìm thấy camera';
            if (err.name === 'NotReadableError') msg = '<i class="fas fa-times-circle text-danger me-1"></i> Camera đang bị chiếm';
            if (err.name === 'NotAllowedError') msg = '<i class="fas fa-times-circle text-danger me-1"></i> Cần cấp quyền camera';
            document.getElementById('camStatusText').innerHTML = msg;
        });
    }

    function stopWebcam() {
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
            currentStream = null;
        }
    }

    function initCamSource() {
        if (selectCamSource.value.startsWith('rtsp')) {
            video.style.display = 'none';
            rtspImg.style.display = 'block';
            let currentUrl = rtspUrl;
            if (selectCamSource.value === 'rtsp_lan') currentUrl = 'rtsp://admin:L2F0C994@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0';
            else if (selectCamSource.value === 'rtsp_wan') currentUrl = 'rtsp://admin:L2F0C994@192.168.1.80:554/cam/realmonitor?channel=1&subtype=0';
            
            rtspUrl = currentUrl;
            rtspImg.src = '/public/api/stream_kiosk?url=' + encodeURIComponent(currentUrl);
            document.getElementById('camStatusText').innerHTML = '<i class="fas fa-network-wired text-info me-1"></i> Đang tải luồng RTSP...';
            rtspImg.onload = () => {
                document.getElementById('cameraBadge').style.display = 'flex';
                document.getElementById('camStatusText').innerHTML = '<i class="fas fa-check-circle text-success me-1"></i> Sẵn sàng (RTSP)';
            };
        } else {
            rtspImg.src = '';
            startWebcam();
        }
    }

    // ===== Pre-Livestream Setup Flow =====
    let processInterval = null;
    let previewStream = null;
    
    const setupScreen = document.getElementById('setupScreen');
    const btnGoLive = document.getElementById('btnGoLive');
    const btnShowConfig = document.getElementById('btnShowConfig');
    
    // Setup controls
    const setupCamSource = document.getElementById('setupCamSource');
    const setupLopId = document.getElementById('setupLopId');
    const setupStartTime = document.getElementById('setupStartTime');
    
    // Preview elements
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
        previewWebcam.style.display = 'none';
        previewWebcam.srcObject = null;
        previewRtsp.style.display = 'none';
        previewRtsp.src = '';
    }
    
    function startPreview() {
        stopPreview();
        previewPlaceholder.classList.remove('d-none');
        previewIcon.classList.add('d-none');
        previewLoading.classList.remove('d-none');
        previewText.innerText = 'Đang kết nối...';
        previewStatus.className = 'badge bg-warning text-dark';
        previewStatus.innerText = 'Đang tải...';

        const source = setupCamSource.value;
        if (source === 'webcam') {
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                previewLoading.classList.add('d-none');
                previewIcon.classList.remove('d-none');
                previewIcon.className = 'fas fa-shield-alt mb-3 text-warning';
                previewText.innerHTML = '<span class="text-warning">Trình duyệt chặn Camera (Cần dùng HTTPS)</span>';
                previewStatus.className = 'badge bg-danger';
                previewStatus.innerText = 'Lỗi Bảo Mật';
                return;
            }
            navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
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

    // Khôi phục giá trị đã lưu cho Setup
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

    // Tự động bật preview khi load trang (nếu đang ở màn hình setup)
    if (setupScreen && setupScreen.style.display !== 'none') {
        startPreview();
    }

    if (btnGoLive) {
        btnGoLive.addEventListener('click', () => {
            if (setupLopId && !setupLopId.value) {
                alert('Vui lòng chọn lớp điểm danh!');
                return;
            }
            
            // Lưu thiết lập
            if (setupLopId) localStorage.setItem('kiosk_lop_id', setupLopId.value);
            if (setupStartTime) localStorage.setItem('kiosk_start_time', setupStartTime.value);
            
            // Dừng preview
            stopPreview();
            
            // Ẩn setup, hiện Kiosk
            setupScreen.classList.remove('d-flex');
            setupScreen.style.display = 'none';
            
            // Đồng bộ config qua cho Kiosk logic chạy
            if (selectCamSource) selectCamSource.value = setupCamSource.value;
            
            const startCheckInterval = setInterval(() => {
                const startTimeStr = setupStartTime ? setupStartTime.value : "07:00";
                const [startH, startM] = startTimeStr.split(':').map(Number);
                const now = new Date();
                const currentH = now.getHours();
                const currentM = now.getMinutes();
                
                if (currentH > startH || (currentH === startH && currentM >= startM)) {
                    clearInterval(startCheckInterval);
                    
                    // Bắt đầu Camera chính
                    document.getElementById('camStatusText').innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Đang bật camera...';
                    initCamSource();
                    
                    // Bắt đầu Interval nhận diện
                    if (!processInterval) {
                        processInterval = setInterval(processFrame, 1500);
                    }
                    
                    // Bật loa
                    const ttsAudio = document.getElementById('ttsAudio');
                    if (ttsAudio) ttsAudio.play().catch(e => {}); 
                } else {
                    document.getElementById('cameraBadge').style.display = 'flex';
                    document.getElementById('camStatusText').innerHTML = `<i class="fas fa-clock text-warning me-1"></i> Đang chờ đến giờ (${startTimeStr})...`;
                }
            }, 1000);
            
            // Lưu interval vào window để có thể clear nếu user bấm Cấu hình lại
            window.kioskStartCheckInterval = startCheckInterval;
        });
    }

    if (btnShowConfig) {
        btnShowConfig.addEventListener('click', () => {
            if (window.kioskStartCheckInterval) {
                clearInterval(window.kioskStartCheckInterval);
            }
            
            // Dừng interval
            if (processInterval) {
                clearInterval(processInterval);
                processInterval = null;
            }
            
            // Dừng camera chính
            stopWebcam();
            if (rtspImg) {
                rtspImg.src = '';
                rtspImg.style.display = 'none';
            }
            
            document.getElementById('cameraBadge').style.display = 'none';
            document.getElementById('camStatusText').innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Đang chờ cấu hình...';
            
            // Show setup screen and start preview
            setupScreen.style.display = 'flex';
            setupScreen.classList.add('d-flex');
            startPreview();
        });
    }

    async function processFrame() {
        if (isProcessing) return;

        // Dùng giá trị từ localStorage hoặc fallback
        const savedLopId = localStorage.getItem('kiosk_lop_id');
        if (!savedLopId) {
            hideScanBox();
            return;
        }

        isProcessing = true;

        const isRtsp = selectCamSource && selectCamSource.value.startsWith('rtsp');
        const sourceElement = isRtsp ? rtspImg : video;

        if (!isRtsp && (!video.videoWidth || !video.videoHeight)) {
            isProcessing = false;
            return;
        }
        if (isRtsp && (!rtspImg.complete || rtspImg.naturalWidth === 0)) {
            isProcessing = false;
            return;
        }

        let reqBody = { 
            lop_id: parseInt(savedLopId),
            start_time: localStorage.getItem('kiosk_start_time') || 'auto'
        };
        let imageData = "";

        if (isRtsp) {
            reqBody.rtsp_url = rtspUrl;
        } else {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            try {
                canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            } catch (e) {
                isProcessing = false; return;
            }
            
            imageData = canvas.toDataURL('image/jpeg', 0.8);
            reqBody.image = imageData;
        }

        try {
            const res = await fetch('/public/api/recognize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '1' },
                body: JSON.stringify(reqBody)
            });
            const data = await res.json();
            const finalImage = data.image || imageData; // Dùng ảnh từ backend nếu có

            if (data.success && data.student) {
                // Luôn cập nhật bounding box để user biết camera vẫn bắt được mặt
                if (data.bbox) updateMask(data.bbox, data.student.ho_ten);

                // Chỉ hiện Panel + Log nếu có record điểm danh thực sự (tránh spam)
                if (data.attendance && data.attendance.action) {
                    const now = Date.now();
                    if (data.student.mssv !== lastMSSV || (now - lastTime) >= 5000) {
                        lastMSSV = data.student.mssv;
                        lastTime = now;
                        showResult(data.student, finalImage, data.bbox);
                    }
                }
            } else {
                hideScanBox();
            }
        } catch (e) {
            console.error(e);
        } finally {
            isProcessing = false;
        }
    }

    function showResult(sv, imgB64, bbox) {
        if (bbox) updateMask(bbox, sv.ho_ten);
        setTimeout(() => { if (Date.now() - lastTime > 1500) hideScanBox(); }, 2000);

        // Update info panel
        document.getElementById('infoEmptyState').style.display = 'none';
        const panel = document.getElementById('infoSuccessState');
        panel.style.display = 'flex';
        panel.style.animation = 'none';
        panel.offsetHeight; // reflow
        panel.style.animation = null;

        document.getElementById('infoAvatar').innerText = sv.ho_ten.charAt(0);
        document.getElementById('infoName').innerText = sv.ho_ten;
        document.getElementById('infoMssv').innerText = sv.mssv;
        document.getElementById('infoClass').innerText = sv.ten_lop || sv.ma_lop || '--';

        const now = new Date();
        const pad = n => (n < 10 ? '0' : '') + n;
        const timeStr = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
        const dateStr = `${now.getDate()}/${now.getMonth()+1}/${now.getFullYear()}`;
        document.getElementById('infoTime').innerText = timeStr;

        addLogEntry(sv, timeStr, dateStr, imgB64);
        
        // Play audio greeting
        speakGreeting(sv.ho_ten);

        // Auto-hide info after 5s if no new face
        setTimeout(() => {
            if (Date.now() - lastTime >= 4500) {
                document.getElementById('infoEmptyState').style.display = 'flex';
                document.getElementById('infoSuccessState').style.display = 'none';
            }
        }, 5000);
    }
    // ===== Unlock Audio =====
    const btnUnlockAudio = document.getElementById('btnUnlockAudio');
    const ttsAudio = document.getElementById('ttsAudio');
    if (btnUnlockAudio) {
        btnUnlockAudio.addEventListener('click', () => {
            ttsAudio.play().catch(e => {}); // Play empty to unlock
            btnUnlockAudio.classList.remove('btn-outline-info');
            btnUnlockAudio.classList.add('btn-info');
            btnUnlockAudio.innerHTML = '<i class="fas fa-volume-up me-1"></i> Loa đã bật';
        });
    }

    // ===== Notification Sound =====
    function speakGreeting(name) {
        if (!ttsAudio) return;
        ttsAudio.src = `/static/audio/success.wav`;
        ttsAudio.play().catch(err => {
            console.log('Auto-play bị chặn, yêu cầu người dùng click nút Bật Loa:', err);
            if (btnUnlockAudio) {
                btnUnlockAudio.classList.add('btn-danger');
                btnUnlockAudio.classList.remove('btn-outline-info', 'btn-info');
            }
        });
    }

    function addLogEntry(sv, timeStr, dateStr, imgB64) {
        const empty = document.getElementById('emptyLogMsg');
        if (empty) empty.remove();

        logCount++;
        document.getElementById('logCounter').innerText = logCount;

        const tr = document.createElement('tr');
        tr.className = 'slide-in-row';
        tr.innerHTML = `
            <td style="padding-left:1.5rem;" class="text-white-50">${logCount}</td>
            <td><img src="${imgB64}" class="img-log shadow-sm" alt="face"></td>
            <td>
                <div class="fw-bold text-white">${sv.ho_ten}</div>
                <div class="small text-white-50"><i class="fas fa-fingerprint me-1"></i>${sv.mssv}</div>
            </td>
            <td class="text-info"><i class="fas fa-layer-group me-1 opacity-75"></i>${sv.ten_lop || sv.ma_lop || '--'}</td>
            <td class="text-success fw-medium"><i class="far fa-clock me-1 opacity-75"></i>${timeStr} <span class="text-white-50 ms-1" style="font-size: 0.85em">${dateStr}</span></td>
        `;
        logList.prepend(tr);
        while (logList.children.length > 50) logList.removeChild(logList.lastChild);
    }

    // ===== Face Tracking Mask =====
    function updateMask(bbox, name) {
        if (!bbox || bbox.length < 4) return;
        scanBox.style.display = 'block';
        scanNameTag.innerText = name;

        const isRtsp = selectCamSource && selectCamSource.value.startsWith('rtsp');
        const srcElem = isRtsp ? rtspImg : video;

        const vW = isRtsp ? srcElem.naturalWidth : srcElem.videoWidth;
        const vH = isRtsp ? srcElem.naturalHeight : srcElem.videoHeight;
        const cW = srcElem.offsetWidth, cH = srcElem.offsetHeight;
        if (!vW || !vH) return;

        const vR = vW / vH, cR = cW / cH;
        let scale, xOff = 0, yOff = 0;
        if (vR > cR) { scale = cH / vH; xOff = (cW - vW * scale) / 2; }
        else          { scale = cW / vW; yOff = (cH - vH * scale) / 2; }

        // Mirror X (video is flipped)
        const mX1 = vW - bbox[2], mX2 = vW - bbox[0];

        const pad = 12;
        scanBox.style.left   = (mX1 * scale + xOff - pad) + 'px';
        scanBox.style.top    = (bbox[1] * scale + yOff - pad) + 'px';
        scanBox.style.width  = ((mX2 - mX1) * scale + pad * 2) + 'px';
        scanBox.style.height = ((bbox[3] - bbox[1]) * scale + pad * 2) + 'px';
    }

    function hideScanBox() {
        scanBox.style.display = 'none';
    }
});