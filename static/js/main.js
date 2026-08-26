// Анимация появления при скролле
(function () {
    var els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window) || !els.length) {
        els.forEach(function (el) { el.classList.add('visible'); });
        return;
    }
    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08 });
    els.forEach(function (el) { io.observe(el); });
})();

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
        btn.classList.add('added');
        setTimeout(function () {
            btn.textContent = original;
            btn.classList.remove('added');
        }, 1200);
    });
});