function filterClasses() {
    const q = document.getElementById('classSearch').value.toLowerCase();
    document.querySelectorAll('.class-card').forEach(card => {
        const text = card.getAttribute('data-search') || '';
        card.style.display = text.includes(q) ? '' : 'none';
    });
}