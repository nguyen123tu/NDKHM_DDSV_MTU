// Simple custom modal logic if Bootstrap modal fails
    function openCustomModal() {
        const modal = document.getElementById('imageModal');
        const content = document.getElementById('imageModalContent');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Trigger reflow
        void modal.offsetWidth;
        
        modal.classList.replace('opacity-0', 'opacity-100');
        content.classList.replace('scale-95', 'scale-100');
    }

    function closeImageModal() {
        const modal = document.getElementById('imageModal');
        const content = document.getElementById('imageModalContent');
        
        modal.classList.replace('opacity-100', 'opacity-0');
        content.classList.replace('scale-100', 'scale-95');
        
        setTimeout(() => {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }, 300);
    }
    
    // Override Bootstrap viewAllImages from external JS if needed, but normally keeping the ID structure allows it to work.
    // If you rewrote JS to not use jQuery/Bootstrap, just fetch and inject.