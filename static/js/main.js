/**
 * Main Layout JavaScript for MTUFace
 */

document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Toggle Logic
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            document.body.classList.toggle('sidebar-collapsed');
            const isCollapsed = document.body.classList.contains('sidebar-collapsed');
            localStorage.setItem('sidebarState', isCollapsed ? 'collapsed' : 'expanded');
        });
    }
});

// Datetime updater
function updateDateTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    const timeDisplay = document.getElementById('timeDisplay');
    if (timeDisplay) {
        timeDisplay.innerText = `${hours}:${minutes}:${seconds}`;
    }
    
    const days = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
    const dayName = days[now.getDay()];
    const date = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    
    const dateDisplay = document.getElementById('dateDisplay');
    if (dateDisplay) {
        dateDisplay.innerText = `${dayName}, ${date}/${month}/${year}`;
    }
}
updateDateTime();
setInterval(updateDateTime, 1000);

// Auto hide flash messages after 5 seconds
setTimeout(() => {
    if (window.jQuery) {
        $('.animate-\\[slideInRight_0\\.4s_ease-out\\]').fadeOut('slow', function() { $(this).remove(); });
    }
}, 5000);

// Global Live Search Logic
document.addEventListener('DOMContentLoaded', () => {
    const globalSearchInput = document.getElementById('globalSearchInput');
    if (globalSearchInput) {
        globalSearchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            // Lọc tất cả các bảng trên trang hiện tại
            const tables = document.querySelectorAll('table tbody');
            
            tables.forEach(tbody => {
                const rows = tbody.querySelectorAll('tr');
                rows.forEach(row => {
                    const rowText = row.innerText.toLowerCase();
                    // Normalize vietnamese characters to search without accents
                    const normalizedText = rowText.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                    const normalizedQuery = query.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                    
                    if (rowText.includes(query) || normalizedText.includes(normalizedQuery)) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        });
    }
});
