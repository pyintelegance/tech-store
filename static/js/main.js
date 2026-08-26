// ===== Тёмная тема =====
(function () {
    var KEY = 'techstore_theme';
    var saved = localStorage.getItem(KEY);
    if (saved === 'dark' || (saved === null && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    var toggle = document.getElementById('theme-toggle');
    if (toggle) {
        var updateIcon = function () {
            toggle.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
        };
        toggle.addEventListener('click', function () {
            var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            if (isDark) {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem(KEY, 'light');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem(KEY, 'dark');
            }
            updateIcon();
        });
        updateIcon();
    }
})();

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

// ===== Тост-уведомления =====
function showToast(message, icon) {
    var container = document.getElementById('toast-container');
    if (!container) return;
    var toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = (icon ? '<span>' + icon + '</span>' : '') + '<span>' + message + '</span>';
    container.appendChild(toast);
    setTimeout(function () {
        toast.classList.add('leaving');
        setTimeout(function () { toast.remove(); }, 300);
    }, 2200);
}

// ===== AJAX добавление в корзину (без перезагрузки) =====
(function () {
    var badge = document.querySelector('.cart-badge');

    function updateBadge(count) {
        if (!badge) {
            var cartLink = document.querySelector('.cart-link');
            if (cartLink) {
                badge = document.createElement('span');
                badge.className = 'cart-badge';
                cartLink.appendChild(badge);
            }
        }
        if (badge) {
            if (count > 0) {
                badge.textContent = count;
                badge.style.display = 'inline-flex';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    function ajaxAdd(form, feedbackEl, cb) {
        var data = new FormData(form);
        data.append('csrf_token', form.querySelector('[name=csrf_token]').value);
        fetch(form.action, {
            method: 'POST',
            body: data,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(function (r) { return r.json(); }).then(function (res) {
            if (res.ok) {
                updateBadge(res.cart_count);
                showToast('🛒 Товар добавлен в корзину');
                if (feedbackEl) {
                    feedbackEl.textContent = '✓';
                    feedbackEl.classList.add('added');
                    setTimeout(function () {
                        feedbackEl.textContent = '+';
                        feedbackEl.classList.remove('added');
                    }, 1200);
                }
            }
            if (cb) cb(res);
        }).catch(function (e) {
            if (cb) cb({ ok: false });
        });
    }

    // Кнопки "+" на карточках каталога и в "похожих товарах"
    document.querySelectorAll('form[action$="/cart/add"]').forEach(function (form) {
        var btn = form.querySelector('.add-btn');
        if (!btn) return;
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            ajaxAdd(form, btn);
        });
    });

    // Страница товара: форма "В корзину" с количеством
    var buyForm = document.querySelector('.buy-form');
    if (buyForm) {
        var submitBtn = buyForm.querySelector('button[type=submit]');
        if (submitBtn) {
            buyForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var original = submitBtn.textContent;
                submitBtn.disabled = true;
                ajaxAdd(buyForm, null, function (res) {
                    submitBtn.disabled = false;
                    if (res.ok) {
                        submitBtn.textContent = '✓';
                        submitBtn.classList.add('added');
                        setTimeout(function () {
                            submitBtn.textContent = original;
                            submitBtn.classList.remove('added');
                        }, 1400);
                    }
                });
            });
        }
    }
})();

// ===== AJAX избранное =====
(function () {
    var wishBadge = document.querySelector('.wish-badge');

    function updateWishBadge(count) {
        if (!wishBadge) {
            var link = document.querySelector('.nav-link[href$="/wishlist"]');
            if (link) {
                wishBadge = document.createElement('span');
                wishBadge.className = 'cart-badge wish-badge';
                link.appendChild(wishBadge);
            }
        }
        if (wishBadge) {
            if (count > 0) {
                wishBadge.textContent = count;
                wishBadge.style.display = 'inline-flex';
            } else {
                wishBadge.style.display = 'none';
            }
        }
    }

    document.querySelectorAll('.wish-form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var btn = form.querySelector('.wish-btn');
            var data = new FormData(form);
            data.append('csrf_token', form.querySelector('[name=csrf_token]').value);
            fetch(form.action, {
                method: 'POST',
                body: data,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            }).then(function (r) { return r.json(); }).then(function (res) {
                if (res.ok) {
                    updateWishBadge(res.wish_count);
                    if (res.added) {
                        btn.classList.add('active');
                        btn.textContent = '♥';
                    } else {
                        btn.classList.remove('active');
                        btn.textContent = '♡';
                        // на странице избранного — удалить карточку
                        var card = form.closest('.card');
                        if (card && card.classList.contains('wish-page')) {
                            card.remove();
                        }
                    }
                }
            }).catch(function () {});
        });
    });
})();

// Управление количеством (+/−): НЕ отправляет форму на странице товара,
// отправляет только на странице корзины (cart_update)
document.querySelectorAll('.qty-control').forEach(function (ctrl) {
    var input = ctrl.querySelector('.qty-input');
    if (!input) return;
    var isCartPage = ctrl.closest('form') && ctrl.closest('form').action.indexOf('/cart/update') !== -1;
    ctrl.querySelectorAll('.qty-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var dir = parseInt(btn.dataset.dir, 10);
            var val = parseInt(input.value, 10) || 1;
            val = Math.max(1, val + dir);
            var max = parseInt(input.max, 10);
            if (max && val > max) val = max;
            input.value = val;
            if (isCartPage) {
                ctrl.closest('form').submit();
            }
        });
    });
});