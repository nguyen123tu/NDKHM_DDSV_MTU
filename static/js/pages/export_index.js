function switchTab(idx) {
    document.querySelectorAll('.export-tab').forEach((t,i) => {
        t.classList.toggle('active', i === idx);
    });
    document.querySelectorAll('.export-panel').forEach((p,i) => {
        p.classList.toggle('active', i === idx);
    });
}

// Format card selection
document.querySelectorAll('.format-card').forEach(card => {
    card.addEventListener('click', function() {
        const group = this.closest('.format-grid');
        group.querySelectorAll('.format-card').forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        this.querySelector('input').checked = true;
    });
});