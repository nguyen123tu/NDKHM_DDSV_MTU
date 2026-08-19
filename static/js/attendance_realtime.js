/**
 * Realtime Attendance JavaScript via Socket.IO
 */

document.addEventListener('DOMContentLoaded', () => {
    // Chỉ kích hoạt khi đang ở trang Live Attendance
    const liveContainer = document.getElementById('live-attendance-container');
    if (!liveContainer) return;

    // Element references
    const formStart = document.getElementById('formStartDetection');
    const startBtn = document.getElementById('btnStart');
    const stopBtn = document.getElementById('btnStop');
    const statusText = document.getElementById('statusText');
    const statusIndicator = document.getElementById('statusIndicator');
    const videoFeed = document.getElementById('videoFeed');
    const logList = document.getElementById('attendanceLog');
    const toastContainer = document.getElementById('toastContainer');

    // Khởi tạo SocketIO
    const socket = io();

    let isRunning = false;
    let isBrowserMode = false;
    let localStream = null;
    let faceApiLoaded = false;
    let detectionInterval = null;
    let lastRecognizeTime = 0;
    let lastMatchInfo = null; // Store last match to display on bounding box

    // face-api.js EAR calculation
    function getEAR(eye) {
        if (!eye || eye.length !== 6) return 0;
        const v1 = Math.hypot(eye[1].x - eye[5].x, eye[1].y - eye[5].y);
        const v2 = Math.hypot(eye[2].x - eye[4].x, eye[2].y - eye[4].y);
        const h = Math.hypot(eye[0].x - eye[3].x, eye[0].y - eye[3].y);
        return (v1 + v2) / (2.0 * h);
    }

    const selectCamId = document.getElementById('selectCamId');
    const customRtspGroup = document.getElementById('customRtspGroup');
    const inputCustomRtsp = document.getElementById('inputCustomRtsp');

    if (selectCamId && customRtspGroup) {
        selectCamId.addEventListener('change', (e) => {
            if (e.target.value === 'custom') {
                customRtspGroup.style.display = 'block';
            } else {
                customRtspGroup.style.display = 'none';
            }
        });
    }

    // Cooldown phía client: tránh spam log panel mỗi frame
    const logCooldowns = {};  // {mssv: timestamp}
    const LOG_COOLDOWN_MS = 5000;  // 5 giây giữa mỗi lần hiển thị cùng 1 MSSV

    // Khi có frame trả về từ Server
    socket.on('frame', (data) => {
        videoFeed.src = data.image;
    });

    // Khi có ai đó được nhận diện (event riêng)
    socket.on('attendance_log', (data) => {
        addLogEntry(data.mssv, data.ho_ten, data.thoi_gian, data.similarity, data.action, data.avatar);
    });

    // Khi có cảnh báo (spoofing)
    socket.on('alert', (data) => {
        showAlert(data.message, data.thoi_gian, data.type);
    });

    // Bắt đầu điểm danh
    formStart.addEventListener('submit', async (e) => {
        e.preventDefault();

        const lopId = document.getElementById('selectLopId').value;
        const camId = document.getElementById('selectCamId').value;

        if (!lopId) {
            alert('Vui lòng chọn lớp để điểm danh!');
            return;
        }

        try {
            startBtn.disabled = true;
            statusText.innerText = "Đang kiểm tra thời gian...";

            let camVal = document.getElementById('selectCamId').value;
            let finalCamId;
            if (camVal === 'custom') {
                finalCamId = document.getElementById('inputCustomRtsp').value.trim();
                if (!finalCamId) {
                    alert('Vui lòng nhập Link RTSP / Camera IP!');
                    startBtn.disabled = false;
                    statusText.innerText = "Chưa khởi động";
                    return;
                }
            } else if (camVal === 'browser') {
                finalCamId = 'browser';
            } else {
                finalCamId = isNaN(camVal) ? camVal : parseInt(camVal);
            }

            const startTimeStr = document.getElementById('inputStartTime') ? document.getElementById('inputStartTime').value : "07:00";
            const [startH, startM] = startTimeStr.split(':').map(Number);

            const doStart = async () => {
                statusText.innerText = "Đang khởi động...";

                isBrowserMode = (finalCamId === 'browser');

                if (isBrowserMode) {
                    // Chạy bằng Webcam trình duyệt & Face-API
                    statusText.innerText = "Đang tải AI Model...";
                    if (!faceApiLoaded) {
                        try {
                            const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1/model/';
                            await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
                            await faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL);
                            faceApiLoaded = true;
                        } catch (e) {
                            alert("Lỗi tải AI Model: " + e);
                            startBtn.disabled = false;
                            return;
                        }
                    }

                    statusText.innerText = "Đang bật Camera...";
                    try {
                        const localVideo = document.getElementById('localVideo');
                        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                        localVideo.srcObject = localStream;
                        localVideo.classList.remove('hidden');
                        document.getElementById('videoFeed').classList.add('hidden');

                        isRunning = true;
                        startBtn.classList.add('hidden');
                        stopBtn.classList.remove('hidden');
                        statusText.innerText = "Hệ thống AI đang hoạt động (Local)";

                        const indicatorBadge = document.getElementById('statusIndicatorBadge');
                        if (indicatorBadge) indicatorBadge.classList.replace('bg-secondary', 'bg-success');

                        showToast('Hệ thống đã sẵn sàng', 'AI Nhận diện trực tiếp trên trình duyệt...', 'success');

                        // Bắt đầu vòng lặp nhận diện
                        startBrowserDetectionLoop();

                    } catch (err) {
                        console.error("Lỗi mở Webcam:", err);
                        let msg = "Không thể mở Webcam trên máy tính của bạn.\n\n";
                        if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                            msg += "🔴 Nguyên nhân (NotFoundError):\n• Máy tính/Laptop của bạn hiện KHÔNG CÓ thiết bị Camera/Webcam nào được cắm vào.\n• Hoặc công tắc vật lý (phím chức năng tắt Camera trên Laptop) đang bị tắt.\n• Hoặc camera bị vô hiệu hóa trong Windows Device Manager.\n\n💡 Cách khắc phục: Hãy cắm Webcam USB, bật phím camera trên máy, hoặc chuyển sang chế độ IP Camera / test trên máy có Webcam.";
                        } else if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                            msg += "🔴 Nguyên nhân (NotAllowedError):\n• Bạn đã từ chối cấp quyền sử dụng Camera trên trình duyệt.\n• Hoặc cài đặt Quyền riêng tư của Windows (Settings > Privacy & security > Camera) đang tắt quyền cho trình duyệt.\n\n💡 Cách khắc phục: Cho phép quyền truy cập Camera trên thanh URL và trong cài đặt Windows.";
                        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
                            msg += "🔴 Nguyên nhân (NotReadableError):\n• Camera đang bị chiếm dụng bởi một ứng dụng khác (Zoom, MS Teams, OBS, Skype...) hoặc một tab trình duyệt khác.\n\n💡 Cách khắc phục: Hãy tắt các phần mềm đang dùng Camera và thử lại.";
                        } else {
                            msg += "🔴 Chi tiết lỗi: " + (err.message || err);
                        }
                        alert("⚠️ LỖI THIẾT BỊ CAMERA\n\n" + msg);
                        statusText.innerText = "Lỗi thiết bị Camera (" + err.name + ")";
                        startBtn.disabled = false;
                    }

                } else {
                    // Chạy bằng IP Camera (Gửi lệnh lên server)
                    const res = await fetch('/attendance/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            lop_id: document.getElementById('selectLopId').value,
                            camera_id: finalCamId,
                            start_time: startTimeStr
                        })
                    });
                    const data = await res.json();

                    if (data.success) {
                        isRunning = true;
                        startBtn.classList.add('hidden');
                        stopBtn.classList.remove('hidden');
                        statusText.innerText = "Hệ thống đang hoạt động";

                        const indicatorBadge = document.getElementById('statusIndicatorBadge');
                        if (indicatorBadge) indicatorBadge.classList.replace('bg-secondary', 'bg-success');

                        showToast('Hệ thống đã sẵn sàng', 'Camera đang hoạt động, bắt đầu điểm danh...', 'success');

                        videoFeed.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 480'%3E%3Crect width='640' height='480' fill='%231e293b'/%3E%3Ctext x='320' y='240' font-family='Arial' font-size='20' fill='%2394a3b8' text-anchor='middle'%3E%C4%90ang tr%E1%BB%A3c camera...%3C/text%3E%3C/svg%3E";
                    } else {
                        alert('Lỗi: ' + data.msg);
                        startBtn.disabled = false;
                        startBtn.classList.remove('hidden');
                        stopBtn.classList.add('hidden');
                        statusText.innerText = "Khởi động thất bại";
                    }
                }
            };

            const checkAndStart = () => {
                const now = new Date();
                const currentH = now.getHours();
                const currentM = now.getMinutes();
                if (currentH > startH || (currentH === startH && currentM >= startM)) {
                    return true;
                }
                return false;
            };

            if (checkAndStart()) {
                await doStart();
            } else {
                startBtn.classList.add('hidden');
                stopBtn.classList.remove('hidden');
                statusText.innerText = `Đang đợi đến giờ (${startTimeStr})...`;

                videoFeed.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 480'%3E%3Crect width='640' height='480' fill='%231e293b'/%3E%3Ctext x='320' y='240' font-family='Arial' font-size='20' fill='%23eab308' text-anchor='middle'%3E%C4%90ang ch%E1%BB%9D %C4%91%E1%BA%BFn gi%E1%BB%9D %C4%91i%E1%BB%83m danh...%3C/text%3E%3C/svg%3E";

                window.waitStartInterval = setInterval(async () => {
                    if (checkAndStart()) {
                        clearInterval(window.waitStartInterval);
                        await doStart();
                    }
                }, 1000);
            }

        } catch (err) {
            console.error(err);
            alert('Lỗi kết nối Server');
            startBtn.disabled = false;
        }
    });

    // Dừng điểm danh
    stopBtn.addEventListener('click', async () => {
        try {
            stopBtn.disabled = true;
            statusText.innerText = "Đang dừng Camera...";

            if (isBrowserMode) {
                if (detectionInterval) clearInterval(detectionInterval);
                if (localStream) {
                    localStream.getTracks().forEach(t => t.stop());
                }
            } else {
                await fetch('/attendance/stop', { method: 'POST' });
            }
            
            // Clean state hoàn toàn bằng cách reload trang để ngắt stream và model AI.
            window.location.reload();

        } catch (err) {
            console.error(err);
            alert('Lỗi kết nối Server');
            stopBtn.disabled = false;
        }
    });

    // --- BROWSER DETECTION LOOP ---
    function startBrowserDetectionLoop() {
        const localVideo = document.getElementById('localVideo');
        const canvas = document.getElementById('overlayCanvas');
        const ctx = canvas.getContext('2d');

        localVideo.addEventListener('play', () => {
            canvas.width = localVideo.videoWidth || 640;
            canvas.height = localVideo.videoHeight || 480;

            detectionInterval = setInterval(async () => {
                if (!isRunning) return;

                // Đồng bộ kích thước canvas
                if (canvas.width !== localVideo.videoWidth && localVideo.videoWidth > 0) {
                    canvas.width = localVideo.videoWidth;
                    canvas.height = localVideo.videoHeight;
                }

                const detections = await faceapi.detectAllFaces(localVideo, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks();

                ctx.clearRect(0, 0, canvas.width, canvas.height);

                let validFaceDetected = false;

                for (const det of detections) {
                    const box = det.detection.box;
                    const landmarks = det.landmarks;

                    // Lấy tọa độ mắt
                    const leftEye = landmarks.getLeftEye();
                    const rightEye = landmarks.getRightEye();
                    const earL = getEAR(leftEye);
                    const earR = getEAR(rightEye);
                    const ear = (earL + earR) / 2.0;

                    const isBlinking = ear < 0.25;
                    
                    let displayText = "Đang quét...";
                    let displayColor = '#FBBF24'; // Màu vàng chờ
                    let boxColor = '#FBBF24';
                    
                    if (isBlinking) {
                        displayText = "Đang phân tích...";
                        displayColor = '#3B82F6'; // Màu xanh dương
                        boxColor = '#3B82F6';
                        validFaceDetected = true;
                    } else {
                        validFaceDetected = true; 
                    }
                    
                    // Hiển thị trạng thái sau khi check backend
                    if (window.lastValidation && (Date.now() - window.lastValidation.time < 4000)) {
                        displayText = window.lastValidation.text;
                        if (window.lastValidation.status === 'success') {
                            displayColor = '#10B981'; // Xanh lá mượt
                            boxColor = '#10B981';
                        } else if (window.lastValidation.status === 'spoofing') {
                            displayColor = '#EF4444'; // Đỏ cảnh báo
                            boxColor = '#EF4444';
                        } else {
                            displayColor = '#F97316'; // Cam cảnh báo
                            boxColor = '#F97316';
                        }
                    }

                    // Vẽ khung dạng góc (Bracket corners) giống máy quét
                    const {x, y, width, height} = box;
                    const len = 30; // độ dài góc
                    ctx.strokeStyle = boxColor;
                    ctx.lineWidth = 4;
                    ctx.lineJoin = 'round';
                    ctx.beginPath();
                    // Top-Left
                    ctx.moveTo(x, y + len); ctx.lineTo(x, y); ctx.lineTo(x + len, y);
                    // Top-Right
                    ctx.moveTo(x + width - len, y); ctx.lineTo(x + width, y); ctx.lineTo(x + width, y + len);
                    // Bottom-Left
                    ctx.moveTo(x, y + height - len); ctx.lineTo(x, y + height); ctx.lineTo(x + len, y + height);
                    // Bottom-Right
                    ctx.moveTo(x + width - len, y + height); ctx.lineTo(x + width, y + height); ctx.lineTo(x + width, y + height - len);
                    ctx.stroke();

                    // Vẽ text nền đen mờ
                    ctx.save();
                    ctx.translate(box.x + box.width / 2, box.y - 15);
                    ctx.scale(-1, 1); // Đảo ngược do camera bị lật
                    
                    ctx.font = "bold 16px 'Inter', sans-serif";
                    ctx.textAlign = "center";
                    const textWidth = ctx.measureText(displayText).width;
                    ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
                    ctx.fillRect(-textWidth/2 - 8, -16, textWidth + 16, 24);
                    
                    ctx.fillStyle = displayColor;
                    ctx.fillText(displayText, 0, 2);
                    ctx.restore();
                }

                // Gửi ảnh lên server nếu phát hiện khuôn mặt hợp lệ
                const now = Date.now();
                if (validFaceDetected && (now - lastRecognizeTime > 2500)) {
                    lastRecognizeTime = now;
                    sendFrameToBackend(localVideo);
                }

            }, 100); // 10 FPS cho frontend detection
        });
    }

    async function sendFrameToBackend(videoElement) {
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.8);

        try {
            const lopId = document.getElementById('selectLopId').value;
            const startTimeStr = document.getElementById('inputStartTime') ? document.getElementById('inputStartTime').value : "07:00";

            const res = await fetch('/public/api/recognize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: dataUrl,
                    lop_id: parseInt(lopId),
                    start_time: startTimeStr
                })
            });
            const data = await res.json();

            if (data.success && data.student) {
                lastMatchInfo = {
                    name: data.student.ho_ten,
                    similarity: data.similarity,
                    time: Date.now()
                };
                
                // Giống event socket 'attendance_log'
                addLogEntry(
                    data.student.mssv,
                    data.student.ho_ten,
                    new Date().toLocaleTimeString('vi-VN', { hour12: false }),
                    data.similarity,
                    data.attendance ? data.attendance.action : 'checkin',
                    data.student.avatar
                );
            } else if (data.msg && data.msg.includes("Giả mạo")) {
                showAlert(data.msg, new Date().toLocaleTimeString('vi-VN'), 'spoofing');
            }
        } catch (e) {
            console.error("Lỗi gửi ảnh lên Server:", e);
        }
    }

    let logCountNum = 0;

    /**
     * Tạo thẻ tr table log và thêm lên đầu danh sách + hiện toast
     */
    function addLogEntry(mssv, name, timeStr, similarity, action, avatarPath) {
        // Cooldown check (tránh lặp lại điểm danh)
        const cooldownInput = document.getElementById('inputCooldown');
        const cooldownSecs = cooldownInput ? parseInt(cooldownInput.value) : 120;
        const cooldownMs = (isNaN(cooldownSecs) ? 120 : cooldownSecs) * 1000;
        const now = Date.now();
        if (logCooldowns[mssv] && (now - logCooldowns[mssv] < cooldownMs)) {
            return; // Đang trong thời gian cooldown, bỏ qua
        }
        logCooldowns[mssv] = now;

        const emptyMsg = document.getElementById('emptyLogMsg');
        if (emptyMsg) emptyMsg.remove();

        logCountNum++;
        const counter = document.getElementById('logCounter');
        if (counter) counter.innerText = logCountNum;

        // Update Info Card Right Panel
        const waitState = document.getElementById('waitState');
        const successState = document.getElementById('successState');

        if (waitState) waitState.classList.add('hidden');
        if (successState) successState.classList.remove('hidden');

        const iMssv = document.getElementById('infoMssv');
        const iName = document.getElementById('infoName');
        const iTime = document.getElementById('infoTime');

        if (iMssv) iMssv.innerText = mssv;
        if (iName) iName.innerText = name;
        if (iTime) iTime.innerText = timeStr;

        // === TOAST NOTIFICATION ===
        const isCheckout = (action === 'checkout');
        const isLate = (action === 'late');
        const isWrongClass = (action === 'wrong_class');

        if (isWrongClass) {
            showToast(`${name} — Khác Lớp!`, `MSSV: ${mssv} không thuộc lớp này`, 'danger');
        } else if (isCheckout) {
            showToast(`${name} — Giờ ra`, `MSSV: ${mssv} • ${timeStr}`, 'warning');
        } else if (isLate) {
            showToast(`${name} — Đi trễ`, `MSSV: ${mssv} • ${timeStr}`, 'danger');
        } else {
            showToast(`${name} — Điểm danh thành công!`, `MSSV: ${mssv} • ${timeStr}`, 'success');
        }

        // Cập nhật banner success timeout (Chỉ hiện nếu không phải wrong_class)
        const successBanner = document.getElementById('successBanner');
        const bannerName = document.getElementById('bannerName');
        if (!isWrongClass && successBanner && bannerName) {
            bannerName.innerText = name;
            successBanner.style.display = 'block';
            setTimeout(() => {
                successBanner.style.display = 'none';
            }, 3000);
        }

        let badgeClass = 'bg-success';
        let badgeText = 'Vào';
        if (isWrongClass) {
            badgeClass = 'bg-danger';
            badgeText = 'Khác lớp';
        } else if (isCheckout) {
            badgeClass = 'bg-warning text-dark';
            badgeText = 'Ra';
        } else if (isLate) {
            badgeClass = 'bg-danger';
            badgeText = 'Trễ';
        }

        const tr = document.createElement('tr');
        tr.className = "slide-in";
        const imgUrl = avatarPath ? `/${avatarPath}` : `/database/${mssv}/0.jpg`;
        const fallbackWord = name.charAt(0).toUpperCase();

        tr.innerHTML = `
            <td class="px-5 py-3 border-b border-outline-variant/50 text-xs font-bold text-on-surface-variant">${logCountNum}</td>
            <td class="px-5 py-3 border-b border-outline-variant/50">
                <div class="flex items-center gap-3">
                    <div class="relative">
                        <img src="${imgUrl}" onerror="this.onerror=null; this.style.display='none'; this.nextElementSibling.style.display='flex';" class="w-8 h-8 rounded-full object-cover border border-outline-variant shadow-sm" />
                        <div class="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-[10px] hidden border border-primary/20">${fallbackWord}</div>
                    </div>
                    <div>
                        <div class="font-bold text-sm text-on-surface leading-tight">${name} <span class="px-1.5 py-0.5 rounded text-[9px] font-bold ml-1 ${badgeClass === 'bg-success' ? 'bg-secondary/10 text-secondary' : badgeClass === 'bg-danger' ? 'bg-error/10 text-error' : 'bg-warning/10 text-warning'}">${badgeText}</span></div>
                        <div class="text-[11px] font-mono text-on-surface-variant mt-0.5">${mssv}</div>
                    </div>
                </div>
            </td>
            <td class="px-5 py-3 border-b border-outline-variant/50 text-right text-xs font-bold text-secondary">${timeStr}</td>
        `;

        logList.prepend(tr);

        while (logList.children.length > 100) {
            logList.removeChild(logList.lastChild);
        }
    }

    /**
     * Thông báo cảnh báo (Spoofing)
     */
    function showAlert(msg, timeStr, type = 'danger') {
        const title = type === 'spoofing' ? '⚠️ Cảnh báo gian lận!' : '⚠️ Cảnh báo!';
        const toastType = type === 'spoofing' ? 'warning' : 'danger';
        showToast(title, msg + ' — ' + timeStr, toastType);

        const tr = document.createElement('tr');
        tr.className = "slide-in bg-danger bg-opacity-10";
        tr.innerHTML = `
            <td colspan="6" class="text-center p-3">
                <i class="fas fa-exclamation-triangle fs-4 text-danger me-2"></i>
                <span class="fw-bold text-danger">${msg}</span>
                <span class="small text-muted ms-2">(${timeStr})</span>
            </td>
        `;

        logList.prepend(tr);
    }

    /**
     * Hiển thị Toast Notification trượt vào từ bên phải
     */
    function showToast(title, message, type = 'success') {
        if (!toastContainer) return;

        const iconMap = {
            success: '<i class="fas fa-check-circle"></i>',
            warning: '<i class="fas fa-sign-out-alt"></i>',
            danger: '<i class="fas fa-exclamation-triangle"></i>'
        };

        const toast = document.createElement('div');
        let borderClass = 'border-l-4 border-green-500';
        let iconBg = 'bg-green-100 text-green-600';
        
        if (type === 'warning') {
            borderClass = 'border-l-4 border-yellow-500';
            iconBg = 'bg-yellow-100 text-yellow-600';
        } else if (type === 'danger') {
            borderClass = 'border-l-4 border-red-500';
            iconBg = 'bg-red-100 text-red-600';
        }

        toast.className = `flex items-center gap-3 bg-surface border border-outline-variant rounded-xl shadow-lg p-4 min-w-[320px] transition-all duration-300 transform translate-x-full ${borderClass}`;
        // Delay to slide in
        setTimeout(() => toast.classList.remove('translate-x-full'), 10);

        toast.innerHTML = `
            <div class="w-10 h-10 rounded-full flex items-center justify-center text-lg shrink-0 ${iconBg}">
                ${iconMap[type] || iconMap.success}
            </div>
            <div class="flex-1">
                <h6 class="text-sm font-bold text-on-surface m-0">${title}</h6>
                <p class="text-xs text-on-surface-variant m-0 mt-0.5">${message}</p>
            </div>
            <button class="text-on-surface-variant hover:text-error transition-colors p-1" 
                    onclick="this.parentElement.classList.add('translate-x-full', 'opacity-0'); setTimeout(() => this.parentElement.remove(), 300);">
                <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
        `;

        toastContainer.appendChild(toast);

        // Play notification sound
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = type === 'success' ? 880 : (type === 'danger' ? 440 : 660);
            gain.gain.value = 0.08;
            osc.start();
            osc.stop(ctx.currentTime + 0.15);
        } catch (e) { }

        // Auto remove after 4s
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('translate-x-full', 'opacity-0');
                setTimeout(() => toast.remove(), 300);
            }
        }, 4000);

        // Keep max 5 toasts
        while (toastContainer.children.length > 5) {
            toastContainer.removeChild(toastContainer.firstChild);
        }
    }
});
