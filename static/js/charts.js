/**
 * Dashboard Charts with Chart.js
 */

document.addEventListener('DOMContentLoaded', () => {
    const chartCanvas = document.getElementById('weeklyChart');
    if (!chartCanvas) return; // Không có thì bỏ qua

    // Cấu hình Chart.js chung cho theme Dark
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Inter';

    // Fetch dữ liệu từ API
    fetch('/api/weekly-chart')
        .then(res => res.json())
        .then(data => {
            const labels = data.map(d => formatDate(d.ngay));
            const coMatData = data.map(d => d.co_mat);
            const canhBaoData = data.map(d => d.canh_bao);

            new Chart(chartCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Lượt Có Mặt',
                            data: coMatData,
                            backgroundColor: 'rgba(163, 100, 243, 0.7)',
                            borderColor: '#a364f3',
                            borderWidth: 1,
                            borderRadius: 4,
                            barPercentage: 0.6
                        },
                        {
                            label: 'Lượt Cảnh Báo',
                            data: canhBaoData,
                            backgroundColor: 'rgba(239, 68, 68, 0.7)',
                            borderColor: '#ef4444',
                            borderWidth: 1,
                            borderRadius: 4,
                            barPercentage: 0.6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleColor: '#fff',
                            bodyColor: '#e2e8f0',
                            borderColor: 'rgba(255,255,255,0.1)',
                            borderWidth: 1,
                            padding: 10
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)',
                                drawBorder: false,
                            },
                            ticks: { precision: 0 }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        })
        .catch(err => console.error("Chart fetch error:", err));
        
    function formatDate(dateStr) {
        // Chuyển "2026-04-14" thành "14/04"
        const parts = dateStr.split('-');
        if (parts.length === 3) {
            return `${parts[2]}/${parts[1]}`;
        }
        return dateStr;
    }
});
