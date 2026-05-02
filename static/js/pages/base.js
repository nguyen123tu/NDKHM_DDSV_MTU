// Prevent sidebar FOUC (flash of unstyled content)
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            document.documentElement.classList.add('sidebar-collapsed');
        }
    

        $(document).ready(function () {
            // Auto ẩn flash msg
            setTimeout(function () {
                $('.alert').fadeOut('slow', function () { $(this).remove(); });
            }, 5000);

            // Cập nhật ngày giờ topbar
            function updateDateTime() {
                const now = new Date();
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                const seconds = String(now.getSeconds()).padStart(2, '0');
                if (document.getElementById('timeDisplay')) {
                    document.getElementById('timeDisplay').innerText = `${hours}:${minutes}:${seconds}`;
                }
                const days = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
                const dayName = days[now.getDay()];
                const date = now.getDate();
                const month = now.getMonth() + 1;
                const year = now.getFullYear();
                if (document.getElementById('dateDisplay')) {
                    document.getElementById('dateDisplay').innerText = `${dayName}, ${date} tháng ${month}, ${year}`;
                }
            }
            updateDateTime();
            setInterval(updateDateTime, 1000);

            // Sidebar Toggle
            const toggleBtn = document.getElementById('sidebarToggle');
            const toggleIcon = document.getElementById('toggleIcon');
            const htmlEl = document.documentElement;

            // Sync icon on initial load
            if (htmlEl.classList.contains('sidebar-collapsed')) {
                if(toggleIcon) toggleIcon.classList.replace('fa-angles-left', 'fa-angles-right');
            }

            function setSidebarState(collapsed) {
                if (collapsed) {
                    htmlEl.classList.add('sidebar-collapsed');
                    if(toggleIcon) toggleIcon.classList.replace('fa-angles-left', 'fa-angles-right');
                } else {
                    htmlEl.classList.remove('sidebar-collapsed');
                    if(toggleIcon) toggleIcon.classList.replace('fa-angles-right', 'fa-angles-left');
                }
                localStorage.setItem('sidebarCollapsed', collapsed);
            }

            if (toggleBtn) {
                toggleBtn.addEventListener('click', () => {
                    setSidebarState(!htmlEl.classList.contains('sidebar-collapsed'));
                });
            }
        });