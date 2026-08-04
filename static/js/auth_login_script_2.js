function togglePassword() {
            const f = document.getElementById('passwordField');
            const i = document.getElementById('toggleIcon');
            if (f.type === 'password') {
                f.type = 'text';
                i.textContent = 'visibility_off';
            } else {
                f.type = 'password';
                i.textContent = 'visibility';
            }
        }