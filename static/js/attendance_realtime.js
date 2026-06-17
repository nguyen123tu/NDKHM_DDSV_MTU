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
            } else {
                finalCamId = isNaN(camVal) ? camVal : parseInt(camVal);
            }

            const startTimeStr = document.getElementById('inputStartTime') ? document.getElementById('inputStartTime').value : "07:00";
            const [startH, startM] = startTimeStr.split(':').map(Number);

            const doStart = async () => {
                statusText.innerText = "Đang khởi động Camera...";
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
                    startBtn.classList.add('d-none');
                    stopBtn.classList.remove('d-none');
                    statusText.innerText = "Hệ thống đang hoạt động";

                    const indicatorBadge = document.getElementById('statusIndicatorBadge');
                    if (indicatorBadge) indicatorBadge.classList.replace('bg-secondary', 'bg-success');

                    showToast('Hệ thống đã sẵn sàng', 'Camera đang hoạt động, bắt đầu điểm danh...', 'success');

                    videoFeed.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 480'%3E%3Crect width='640' height='480' fill='%231e293b'/%3E%3Ctext x='320' y='240' font-family='Arial' font-size='20' fill='%2394a3b8' text-anchor='middle'%3E%C4%90ang tr%E1%BB%A3c camera...%3C/text%3E%3C/svg%3E";
                } else {
                    alert('Lỗi: ' + data.msg);
                    startBtn.disabled = false;
                    startBtn.classList.remove('d-none');
                    stopBtn.classList.add('d-none');
                    statusText.innerText = "Khởi động thất bại";
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
                startBtn.classList.add('d-none');
                stopBtn.classList.remove('d-none');
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
            if (window.waitStartInterval) clearInterval(window.waitStartInterval);
            
            stopBtn.disabled = true;
            statusText.innerText = "Đang dừng Camera...";

            await fetch('/attendance/stop', { method: 'POST' });

            isRunning = false;
            stopBtn.classList.add('d-none');
            startBtn.classList.remove('d-none');
            startBtn.disabled = false;

            statusText.innerText = "Hệ thống đã dừng";
            const indicatorBadge = document.getElementById('statusIndicatorBadge');
            if (indicatorBadge) {
                indicatorBadge.classList.remove('bg-success');
                indicatorBadge.classList.add('bg-secondary');
            }

            showToast('Đã dừng hệ thống', 'Camera và nhận diện đã tắt.', 'warning');

            videoFeed.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 480'%3E%3Crect width='640' height='480' fill='%23000'/%3E%3Ctext x='320' y='240' font-family='Arial' font-size='24' fill='%23fff' text-anchor='middle'%3ECamera %C4%91%C3%A3 t%E1%BA%AFt%3C/text%3E%3C/svg%3E";

        } catch (err) {
            console.error(err);
            alert('Lỗi kết nối Server');
            stopBtn.disabled = false;
        }
    });

    let logCountNum = 0;

    /**
     * Tạo thẻ tr table log và thêm lên đầu danh sách + hiện toast
     */
    function addLogEntry(mssv, name, timeStr, similarity, action, avatarPath) {
        const emptyMsg = document.getElementById('emptyLogMsg');
        if (emptyMsg) emptyMsg.remove();

        logCountNum++;
        const counter = document.getElementById('logCounter');
        if (counter) counter.innerText = logCountNum;

        // Update Info Card Right Panel
        const waitState = document.getElementById('waitState');
        const successState = document.getElementById('successState');

        if (waitState) waitState.classList.add('d-none');
        if (successState) successState.classList.remove('d-none');

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
            <td class="text-start ps-4 fw-bold text-muted">${logCountNum}</td>
            <td class="text-start fw-bold text-primary">${mssv}</td>
            <td class="text-start fw-medium">${name}</td>
            <td><span class="badge ${badgeClass}">${badgeText}</span></td>
            <td class="text-success fw-medium">${timeStr}</td>
            <td class="text-center">
                <div class="position-relative d-inline-block">
                    <img src="${imgUrl}" 
                         onerror="this.onerror=null; this.style.display='none'; this.nextElementSibling.style.display='flex';" 
                         class="rounded-circle object-fit-cover border border-light shadow-sm" 
                         style="width: 38px; height: 38px; background: #fff;" 
                    />
                    <div class="avatar bg-primary text-white justify-content-center align-items-center rounded-circle" 
                         style="width: 38px; height: 38px; font-weight: bold; font-size: 0.9rem; display: none;">
                        ${fallbackWord}
                    </div>
                </div>
            </td>
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
        toast.className = `attendance-toast ${type === 'warning' ? 'toast-checkout' : ''} ${type === 'danger' ? 'toast-alert' : ''}`;
        toast.innerHTML = `
            <div class="toast-icon ${type}">${iconMap[type] || iconMap.success}</div>
            <div class="toast-body">
                <h6>${title}</h6>
                <p>${message}</p>
            </div>
            <button class="toast-close" onclick="this.parentElement.classList.add('toast-out'); setTimeout(() => this.parentElement.remove(), 300);">
                <i class="fas fa-times"></i>
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
            toast.classList.add('toast-out');
            setTimeout(() => toast.remove(), 300);
        }, 4000);

        // Keep max 5 toasts
        while (toastContainer.children.length > 5) {
            toastContainer.removeChild(toastContainer.firstChild);
        }
    }
});
