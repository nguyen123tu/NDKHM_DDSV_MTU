function showEvidenceModal(checkin, checkout, name, mssv) {
        document.getElementById('modalStudentName').innerText = name;
        document.getElementById('modalStudentMssv').innerText = `MSSV: ${mssv}`;
        
        const checkinImg = document.getElementById('modalCheckinImg');
        const checkinEmpty = document.getElementById('modalCheckinEmpty');
        if (checkin) {
            checkinImg.src = '/' + checkin;
            checkinImg.classList.remove('hidden');
            checkinEmpty.classList.add('hidden');
        } else {
            checkinImg.classList.add('hidden');
            checkinEmpty.classList.remove('hidden');
        }
        
        const checkoutImg = document.getElementById('modalCheckoutImg');
        const checkoutEmpty = document.getElementById('modalCheckoutEmpty');
        if (checkout) {
            checkoutImg.src = '/' + checkout;
            checkoutImg.classList.remove('hidden');
            checkoutEmpty.classList.add('hidden');
        } else {
            checkoutImg.classList.add('hidden');
            checkoutEmpty.classList.remove('hidden');
        }

        const modal = document.getElementById('evidenceModal');
        const modalContent = document.getElementById('evidenceModalContent');
        modal.classList.remove('hidden');
        setTimeout(() => {
            modal.classList.remove('opacity-0');
            modalContent.classList.remove('scale-95');
        }, 10);
    }

    function closeEvidenceModal() {
        const modal = document.getElementById('evidenceModal');
        const modalContent = document.getElementById('evidenceModalContent');
        modal.classList.add('opacity-0');
        modalContent.classList.add('scale-95');
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }