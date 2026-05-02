function togglePassword() {
            const pwdField = document.getElementById('passwordField');
            const icon = document.getElementById('toggleIcon');
            if (pwdField.type === 'password') {
                pwdField.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                pwdField.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        }