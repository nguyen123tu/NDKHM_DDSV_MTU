// Xử lý chuyển tab
    function switchTab(index) {
        // Reset tất cả tab styles
        document.querySelectorAll('.export-tab').forEach(tab => {
            tab.classList.remove('border-primary', 'border-secondary', 'border-tertiary', 'shadow-md');
            tab.classList.add('border-transparent');
            tab.querySelector('.tab-check').classList.remove('opacity-100');
            tab.querySelector('.tab-check').classList.add('opacity-0');
        });
        
        // Hide all panels
        document.querySelectorAll('.export-panel').forEach(panel => {
            panel.classList.remove('active');
        });

        // Set active tab & panel
        const activeTab = document.getElementById(`tab-${index}`);
        const activePanel = document.getElementById(`panel-${index}`);
        
        activePanel.classList.add('active');
        
        if(index === 0) {
            activeTab.classList.replace('border-transparent', 'border-primary');
            activeTab.classList.add('shadow-md');
        } else if(index === 1) {
            activeTab.classList.replace('border-transparent', 'border-secondary');
            activeTab.classList.add('shadow-md');
        } else if(index === 2) {
            activeTab.classList.replace('border-transparent', 'border-tertiary');
            activeTab.classList.add('shadow-md');
        }
        activeTab.querySelector('.tab-check').classList.replace('opacity-0', 'opacity-100');
    }

    // Xử lý chọn format
    function updateFormatUI(format) {
        const xlLabel = document.getElementById('format-excel');
        const pdfLabel = document.getElementById('format-pdf');
        const xlCheck = document.getElementById('format-check-excel');
        const pdfCheck = document.getElementById('format-check-pdf');

        if(format === 'excel') {
            xlLabel.classList.replace('border-outline-variant', 'border-primary');
            xlLabel.classList.add('bg-primary/5');
            xlCheck.classList.replace('opacity-0', 'opacity-100');

            pdfLabel.classList.replace('border-error', 'border-outline-variant');
            pdfLabel.classList.remove('bg-error/5');
            pdfCheck.classList.replace('opacity-100', 'opacity-0');
        } else {
            pdfLabel.classList.replace('border-outline-variant', 'border-error');
            pdfLabel.classList.add('bg-error/5');
            pdfCheck.classList.replace('opacity-0', 'opacity-100');

            xlLabel.classList.replace('border-primary', 'border-outline-variant');
            xlLabel.classList.remove('bg-primary/5');
            xlCheck.classList.replace('opacity-100', 'opacity-0');
        }
    }