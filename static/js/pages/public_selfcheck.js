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

    // Start Camera
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
    .then(stream => {
        video.srcObject = stream;
        document.getElementById('cameraBadge').style.display = 'flex';
        document.getElementById('camStatusText').innerHTML = '<i class="fas fa-check-circle text-success me-1"></i> Sẵn sàng';
        setInterval(processFrame, 1500);
    })
    .catch(() => {
        document.getElementById('camStatusText').innerHTML = '<i class="fas fa-times-circle text-danger me-1"></i> Không truy cập được camera';
    });

    async function processFrame() {
        if (isProcessing) return;

        const lopId = document.getElementById('selectLopId').value;
        if (!lopId) {
            // Chưa chọn lớp thì không nhận diện để tránh log nhầm
            hideScanBox();
            document.getElementById('infoEmptyState').style.display = 'flex';
            document.getElementById('infoSuccessState').style.display = 'none';
            return;
        }

        isProcessing = true;

        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 480;
        canvas.getContext('2d').drawImage(video, 0, 0);
        const imageData = canvas.toDataURL('image/jpeg', 0.8);

        try {
            const res = await fetch('/public/api/recognize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData, lop_id: parseInt(lopId) })
            });
            const data = await res.json();

            if (data.success && data.student) {
                // Luôn cập nhật bounding box để user biết camera vẫn bắt được mặt
                if (data.bbox) updateMask(data.bbox, data.student.ho_ten);

                // Chỉ hiện Panel + Log nếu có record điểm danh thực sự (tránh spam)
                if (data.attendance && data.attendance.action) {
                    const now = Date.now();
                    if (data.student.mssv !== lastMSSV || (now - lastTime) >= 5000) {
                        lastMSSV = data.student.mssv;
                        lastTime = now;
                        showResult(data.student, imageData, data.bbox);
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

        // Auto-hide info after 5s if no new face
        setTimeout(() => {
            if (Date.now() - lastTime >= 4500) {
                document.getElementById('infoEmptyState').style.display = 'flex';
                document.getElementById('infoSuccessState').style.display = 'none';
            }
        }, 5000);
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

        const vW = video.videoWidth, vH = video.videoHeight;
        const cW = video.offsetWidth, cH = video.offsetHeight;
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