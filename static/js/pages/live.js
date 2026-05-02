document.addEventListener("DOMContentLoaded", function() {
        const badge = document.getElementById('statusIndicatorBadge');
        const text = document.getElementById('statusText');
        badge.classList.replace('cam-status-offline', 'cam-status-online');
        text.innerText = "Camera đang hoạt động";
    });