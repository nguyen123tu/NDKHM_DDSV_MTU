// Toggle Custom RTSP Input
    document.getElementById('selectCamId').addEventListener('change', function () {
        const rtspGroup = document.getElementById('customRtspGroup');
        if (this.value === 'custom') {
            rtspGroup.style.display = 'block';
        } else {
            rtspGroup.style.display = 'none';
        }
    });

    // Observer to toggle scan line animation
    const btnStart = document.getElementById('btnStart');
    const scanLineAnim = document.getElementById('scanLineAnim');
    const statusIndicator = document.getElementById('statusIndicator');

    // Quick hack to hook into existing JS logic:
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'class') {
                if (btnStart.classList.contains('hidden') || btnStart.classList.contains('d-none')) {
                    // Is running
                    scanLineAnim.style.opacity = '1';
                    statusIndicator.classList.replace('bg-error', 'bg-secondary');
                } else {
                    // Stopped
                    scanLineAnim.style.opacity = '0';
                    statusIndicator.classList.replace('bg-secondary', 'bg-error');
                }
            }
        });
    });
    observer.observe(btnStart, { attributes: true });