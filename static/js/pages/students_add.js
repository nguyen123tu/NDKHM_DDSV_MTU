function previewImage(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('avatarPreview').src = e.target.result;
            document.getElementById('avatarPreview').classList.remove('d-none');
            document.getElementById('avatarIcon').classList.add('d-none');
        }
        reader.readAsDataURL(input.files[0]);
    }
}