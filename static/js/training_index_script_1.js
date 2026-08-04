// CSS Toggle cho panel
    const btnTrainAll = document.getElementById('btnTrainAll');
    const idlePanel = document.getElementById('idlePanel');
    const progressPanel = document.getElementById('progressPanel');

    // Override hoặc móc vào logic cũ nếu cần thiết. Logic gửi ajax được nằm ở static/js/pages/training_index.js
    // Ở file JS cũ, nó truy xuất #idlePanel và #progressPanel thông qua d-none, d-block (bootstrap). 
    // Mình sẽ tạo MutationObserver hoặc patch lại JS một chút tại đây nếu cần thiết, 
    // hoặc thêm helper toggle class cho Tailwind.
    
    function showProgress() {
        idlePanel.classList.add('opacity-0');
        setTimeout(() => {
            idlePanel.classList.add('hidden');
            idlePanel.classList.remove('flex');
            
            progressPanel.classList.remove('pointer-events-none', 'z-0');
            progressPanel.classList.add('z-10');
            progressPanel.classList.remove('opacity-0');
        }, 300);
    }

    function hideProgress() {
        progressPanel.classList.add('opacity-0');
        setTimeout(() => {
            progressPanel.classList.add('pointer-events-none', 'z-0');
            progressPanel.classList.remove('z-10');
            
            idlePanel.classList.remove('hidden');
            idlePanel.classList.add('flex');
            // reflow
            void idlePanel.offsetWidth;
            idlePanel.classList.remove('opacity-0');
        }, 300);
    }
    
    // Ghi đè phương thức cũ trong trường hợp training_index.js dùng jQuery show/hide:
    // Có thể tạm thời bỏ qua vì JS cũ sẽ thêm style="display: none" hoặc d-none, vẫn hoạt động với Tailwind nếu ta kiểm soát tốt.