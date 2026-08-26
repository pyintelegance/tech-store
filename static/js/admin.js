// Admin: авто-скрытие flash-сообщений
document.querySelectorAll('.alert').forEach(function (el) {
    setTimeout(function () {
        el.style.transition = 'opacity .4s';
        el.style.opacity = '0';
        setTimeout(function () { el.remove(); }, 400);
    }, 4000);
});

// Admin: предпросмотр выбранного изображения
var fileInput = document.getElementById('image_file');
var preview = document.getElementById('img-preview');
if (fileInput && preview) {
    fileInput.addEventListener('change', function () {
        var file = fileInput.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    });
}