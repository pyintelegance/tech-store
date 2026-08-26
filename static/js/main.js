// Управление количеством (+/−) в формах
document.querySelectorAll('.qty-control').forEach(function (ctrl) {
    var input = ctrl.querySelector('.qty-input');
    if (!input) return;
    ctrl.querySelectorAll('.qty-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var dir = parseInt(btn.dataset.dir, 10);
            var val = parseInt(input.value, 10) || 1;
            val = Math.max(1, val + dir);
            var max = parseInt(input.max, 10);
            if (max && val > max) val = max;
            input.value = val;
            // авто-отправка формы (на странице корзины)
            if (ctrl.closest('form')) {
                ctrl.closest('form').submit();
            }
        });
    });
});

// Кнопка «Добавлено» — визуальный фидбек
document.querySelectorAll('.add-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
        var original = btn.textContent;
        btn.textContent = '✓';
        btn.style.background = '#16a34a';
        btn.style.borderColor = '#16a34a';
        btn.style.color = '#fff';
        setTimeout(function () {
            btn.textContent = original;
            btn.style.background = '';
            btn.style.borderColor = '';
            btn.style.color = '';
        }, 1200);
    });
});
