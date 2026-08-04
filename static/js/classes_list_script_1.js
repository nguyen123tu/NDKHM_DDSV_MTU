function filterClasses() {
        const query = document.getElementById('classSearch').value.toLowerCase();
        const cards = document.querySelectorAll('.class-card');
        cards.forEach(card => {
            const data = card.getAttribute('data-search');
            if (data.includes(query)) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    }