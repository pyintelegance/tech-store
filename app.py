# -*- coding: utf-8 -*-
"""Магазин техники tech-store — Flask + PostgreSQL.

Слои:
  config.py      — настройки
  database.py    — подключения к БД
  repository.py  — SQL-запросы
  forms.py       — формы с валидацией (WTForms)
  app.py         — роуты, CSRF, админ-панель
"""
import functools
import json
import os
import secrets
import uuid
from decimal import Decimal, InvalidOperation

from flask import (Flask, render_template, request, redirect, url_for,
                   session, abort, flash, jsonify)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

import config
import database as db
import repository as repo
from database import get_conn
from forms import (csrf, CheckoutForm, LoginForm, ProductForm,
                   CategoryForm, CityForm, CouponForm)

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["WTF_CSRF_TIME_LIMIT"] = None
app.config["WTF_CSRF_SSL_STRICT"] = False
csrf.init_app(app)

TRANSLATIONS = {
    "ru": {
        "brand": "TechStore",
        "tagline": "Оригинальная техника с доставкой по Узбекистану",
        "catalog": "Каталог",
        "cart": "Корзина",
        "search_placeholder": "Поиск: iPhone, ноутбук, наушники...",
        "search_btn": "Найти",
        "all": "Все",
        "sort_popular": "Популярные",
        "sort_cheap": "Дешевле",
        "sort_expensive": "Дороже",
        "sort_rating": "По рейтингу",
        "buy": "В корзину",
        "added": "Добавлено",
        "empty_catalog": "Ничего не найдено",
        "empty_catalog_hint": "Попробуйте изменить запрос",
        "details": "Подробнее",
        "in_stock": "В наличии",
        "out_of_stock": "Нет в наличии",
        "reviews": "отзывов",
        "description": "Описание",
        "cart_title": "Корзина",
        "cart_empty": "Ваша корзина пуста",
        "cart_empty_hint": "Перейдите в каталог и выберите товары",
        "go_catalog": "Перейти в каталог",
        "product": "Товар",
        "price": "Цена",
        "qty": "Кол-во",
        "total": "Итого",
        "delivery": "Доставка",
        "items_total": "Товары",
        "checkout": "Оформить заказ",
        "order_title": "Оформление заказа",
        "your_info": "Ваши данные",
        "name": "Имя и фамилия",
        "phone": "Телефон",
        "city": "Город",
        "city_placeholder": "Выберите город",
        "address": "Адрес доставки (обязательно)",
        "address_ph": "Улица, дом, квартира",
        "address2": "Дополнительный адрес (необязательно)",
        "address2_ph": "Ориентир, подъезд, этаж",
        "pay_on_delivery": "Оплата при получении",
        "delivery_speed": "Приблизительное время доставки",
        "minutes": "мин",
        "place_order": "Подтвердить заказ",
        "back_cart": "Назад в корзину",
        "order_success_title": "Заказ оформлен!",
        "order_success_text": "Спасибо! Ваш заказ принят. Мы свяжемся с вами по телефону.",
        "order_number": "Номер заказа",
        "order_summary": "Состав заказа",
        "continue_shopping": "Продолжить покупки",
        "remove": "Удалить",
        "ru": "Рус",
        "uz": "Узб",
        "footer_text": "© 2026 TechStore. Оригинальная техника.",
        "admin": "Админ",
        "login_title": "Вход для администратора",
        "username": "Логин",
        "password": "Пароль",
        "login": "Войти",
        "logout": "Выйти",
        "orders": "Заказы",
        "products": "Товары",
        "categories": "Категории",
        "cities": "Доставка",
        "date": "Дата",
        "customer": "Клиент",
        "status": "Статус",
        "new": "Новый",
        "processing": "В обработке",
        "delivered": "Доставлен",
        "cancelled": "Отменён",
        "status_new": "Новый",
        "status_processing": "В обработке",
        "status_delivered": "Доставлен",
        "status_cancelled": "Отменён",
        "add_product": "Добавить товар",
        "edit": "Редактировать",
        "delete": "Удалить",
        "save": "Сохранить",
        "back": "Назад",
        "image": "Картинка",
        "stock": "Остаток",
        "rating": "Рейтинг",
        "reviews_count": "Отзывы",
        "confirm_delete": "Удалить?",
        "orders_list": "Список заказов",
        "address2_label": "Доп. адрес",
        "items": "Состав",
        "invalid_credentials": "Неверный логин или пароль",
        "logged_out": "Вы вышли",
        "not_found": "Страница не найдена",
        "error_hint": "Вернуться на главную",
        "price_from": "Цена от",
        "price_to": "Цена до",
        "apply": "Применить",
        "reset": "Сбросить",
        "name_required": "Укажите имя",
        "phone_required": "Укажите телефон",
        "phone_invalid": "Некорректный телефон",
        "city_required": "Выберите город",
        "address_required": "Укажите адрес",
        "address_length": "Адрес слишком короткий",
        "delivery_price_label": "Цена доставки",
        "delivery_minutes_label": "Время доставки (мин)",
        "city_name": "Город",
        "product_saved": "Товар сохранён",
        "product_deleted": "Товар удалён",
        "category_saved": "Категория сохранена",
        "category_deleted": "Категория удалена",
        "city_saved": "Город сохранён",
        "city_deleted": "Город удалён",
        "status_updated": "Статус обновлён",
        "price_min_required": "Укажите цену от",
        "price_max_required": "Укажите цену до",
        "topbar_delivery": "Быстрая доставка по Узбекистану",
        "topbar_secure": "Оплата при получении",
        "help": "Помощь",
        "contacts": "Контакты",
        "features_title": "Почему выбирают нас",
        "features_sub": "Надёжность и сервис — наша главная ценность",
        "feature1_title": "Оригинальная техника",
        "feature1_text": "Только проверенные товары с официальной гарантией производителя",
        "feature2_title": "Быстрая доставка",
        "feature2_text": "Доставим заказ в любой город Узбекистана в кратчайшие сроки",
        "feature3_title": "Оплата при получении",
        "feature3_text": "Проверьте товар перед оплатой — платите только после получения",
        "feature4_title": "Поддержка 24/7",
        "feature4_text": "Наши менеджеры всегда готовы помочь с выбором и оформлением",
        "hero_badge": "Только оригинальная техника",
        "hero_title": "Техника, которая меняет",
        "hero_title_accent": "жизнь к лучшему",
        "hero_sub": "Смартфоны, ноутбуки, ТВ и аксессуары от мировых брендов. Официальная гарантия, честные цены и быстрая доставка по Узбекистану.",
        "hero_cta": "Смотреть каталог",
        "hero_ghost": "О нас",
        "stat_products": "товаров",
        "stat_delivery": "городов доставки",
        "stat_clients": "довольных клиентов",
        "card_guarantee": "Официальная гарантия",
        "card_delivery": "Доставка по городам",
        "card_payment": "Оплата при получении",
        "card_original": "Только оригинал",
        "popular_title": "Хиты продаж",
        "all_title": "Каталог товаров",
        "reviews_title": "Отзывы покупателей",
        "write_review": "Оставить отзыв",
        "your_name": "Ваше имя",
        "your_rating": "Оценка",
        "your_review": "Ваш отзыв",
        "send_review": "Отправить отзыв",
        "review_submitted": "Спасибо! Отзыв отправлен на проверку",
        "no_reviews": "Отзывов пока нет — будьте первым!",
        "specs_title": "Характеристики",
        "gallery": "Фотографии",
        "coupon": "Промокод",
        "coupon_ph": "Например: WELCOME10",
        "coupon_apply": "Применить",
        "coupon_applied": "Промокод применён",
        "coupon_invalid": "Промокод не найден",
        "coupon_remove": "Убрать",
        "discount": "Скидка",
        "subtotal": "Товары",
        "dashboard": "Дашборд",
        "analytics": "Аналитика",
        "stat_orders": "Заказов",
        "stat_revenue": "Выручка",
        "stat_new": "Новые",
        "stat_products_admin": "Товаров",
        "stat_reviews": "Отзывов",
        "sales_14d": "Продажи за 14 дней",
        "top_products": "Топ товаров",
        "recent_orders": "Последние заказы",
        "review_approved": "Отзыв одобрен",
        "review_deleted": "Отзыв удалён",
        "coupon_saved": "Промокод сохранён",
        "coupon_deleted": "Промокод удалён",
        "coupons_list": "Промокоды",
        "code": "Код",
        "percent": "Скидка %",
        "active": "Активен",
        "disabled": "Выключен",
        "toggle": "Вкл/выкл",
        "add_coupon": "Добавить промокод",
        "specs_label": "Характеристики (каждая строка: Ключ: значение)",
        "gallery_label": "Дополнительные фото (несколько)",
    },
    "uz": {
        "brand": "TechStore",
        "tagline": "O'zbekiston bo'ylab yetkazib berish bilan original texnika",
        "catalog": "Katalog",
        "cart": "Savat",
        "search_placeholder": "Qidirish: iPhone, noutbuk, quloqchin...",
        "search_btn": "Topish",
        "all": "Barchasi",
        "sort_popular": "Ommabop",
        "sort_cheap": "Arzon",
        "sort_expensive": "Qimmat",
        "sort_rating": "Reyting bo'yicha",
        "buy": "Savatga",
        "added": "Qo'shildi",
        "empty_catalog": "Hech narsa topilmadi",
        "empty_catalog_hint": "So'rovni o'zgartirib ko'ring",
        "details": "Batafsil",
        "in_stock": "Bor",
        "out_of_stock": "Yo'q",
        "reviews": "ta sharh",
        "description": "Tavsif",
        "cart_title": "Savat",
        "cart_empty": "Savatingiz bo'sh",
        "cart_empty_hint": "Katalogga o'tib, tovarlarni tanlang",
        "go_catalog": "Katalogga o'tish",
        "product": "Mahsulot",
        "price": "Narx",
        "qty": "Soni",
        "total": "Jami",
        "delivery": "Yetkazib berish",
        "items_total": "Mahsulotlar",
        "checkout": "Buyurtma berish",
        "order_title": "Buyurtma rasmiylashtirish",
        "your_info": "Sizning ma'lumotlaringiz",
        "name": "Ism va familiya",
        "phone": "Telefon",
        "city": "Shahar",
        "city_placeholder": "Shaharni tanlang",
        "address": "Yetkazib berish manzili (majburiy)",
        "address_ph": "Ko'cha, uy, xonadon",
        "address2": "Qo'shimcha manzil (ixtiyoriy)",
        "address2_ph": "Mo'ljal, kirish, qavat",
        "pay_on_delivery": "Olganda to'lash",
        "delivery_speed": "Yetkazib berish vaqti",
        "minutes": "daq",
        "place_order": "Buyurtmani tasdiqlash",
        "back_cart": "Savatga qaytish",
        "order_success_title": "Buyurtma qabul qilindi!",
        "order_success_text": "Rahmat! Buyurtmangiz qabul qilindi. Siz bilan telefon orqali bog'lanamiz.",
        "order_number": "Buyurtma raqami",
        "order_summary": "Buyurtma tarkibi",
        "continue_shopping": "Xaridni davom ettirish",
        "remove": "O'chirish",
        "ru": "Рус",
        "uz": "Uzb",
        "footer_text": "© 2026 TechStore. Original texnika.",
        "admin": "Admin",
        "login_title": "Administrator uchun kirish",
        "username": "Login",
        "password": "Parol",
        "login": "Kirish",
        "logout": "Chiqish",
        "orders": "Buyurtmalar",
        "products": "Mahsulotlar",
        "categories": "Kategoriyalar",
        "cities": "Yetkazib berish",
        "date": "Sana",
        "customer": "Mijoz",
        "status": "Holat",
        "new": "Yangi",
        "processing": "Jarayonda",
        "delivered": "Yetkazildi",
        "cancelled": "Bekor qilindi",
        "status_new": "Yangi",
        "status_processing": "Jarayonda",
        "status_delivered": "Yetkazildi",
        "status_cancelled": "Bekor qilindi",
        "add_product": "Mahsulot qo'shish",
        "edit": "Tahrirlash",
        "delete": "O'chirish",
        "save": "Saqlash",
        "back": "Orqaga",
        "image": "Rasm",
        "stock": "Qoldiq",
        "rating": "Reyting",
        "reviews_count": "Sharhlar",
        "confirm_delete": "O'chirish?",
        "orders_list": "Buyurtmalar ro'yxati",
        "address2_label": "Qo'shimcha manzil",
        "items": "Tarkib",
        "invalid_credentials": "Login yoki parol noto'g'ri",
        "logged_out": "Chiqdingiz",
        "not_found": "Sahifa topilmadi",
        "error_hint": "Bosh sahifaga qaytish",
        "price_from": "Narx dan",
        "price_to": "Narx gacha",
        "apply": "Qo'llash",
        "reset": "Tozalash",
        "name_required": "Ismni kiriting",
        "phone_required": "Telefonni kiriting",
        "phone_invalid": "Telefon noto'g'ri",
        "city_required": "Shaharni tanlang",
        "address_required": "Manzilni kiriting",
        "address_length": "Manzil juda qisqa",
        "delivery_price_label": "Yetkazib berish narxi",
        "delivery_minutes_label": "Yetkazib berish vaqti (daq)",
        "city_name": "Shahar",
        "product_saved": "Mahsulot saqlandi",
        "product_deleted": "Mahsulot o'chirildi",
        "category_saved": "Kategoriya saqlandi",
        "category_deleted": "Kategoriya o'chirildi",
        "city_saved": "Shahar saqlandi",
        "city_deleted": "Shahar o'chirildi",
        "status_updated": "Holat yangilandi",
        "price_min_required": "Narx dan kiriting",
        "price_max_required": "Narx gacha kiriting",
        "topbar_delivery": "O'zbekiston bo'ylab tez yetkazib berish",
        "topbar_secure": "Olganda to'lash",
        "help": "Yordam",
        "contacts": "Aloqa",
        "features_title": "Nega bizni tanlashadi",
        "features_sub": "Ishonchlilik va xizmat — bizning asosiy qadriyatimiz",
        "feature1_title": "Original texnika",
        "feature1_text": "Faqat rasmiy kafolatli tasdiqlangan tovarlar",
        "feature2_title": "Tez yetkazib berish",
        "feature2_text": "Buyurtmani O'zbekistonning istalgan shahriga tez yetkazamiz",
        "feature3_title": "Olganda to'lash",
        "feature3_text": "To'lovdan oldin tovarni tekshiring — faqat olganda to'lang",
        "feature4_title": "24/7 qo'llab-quvvatlash",
        "feature4_text": "Menejerlarimiz tanlash va rasmiylashtirishda yordam berishga tayyor",
        "hero_badge": "Faqat original texnika",
        "hero_title": "Hayotni o'zgartiradigan",
        "hero_title_accent": "texnika",
        "hero_sub": "Jahon brendlaridan smartfonlar, noutbuklar, televizorlar va aksessuarlar. Rasmiy kafolat, halol narxlar va O'zbekiston bo'ylab tez yetkazib berish.",
        "hero_cta": "Katalogni ko'rish",
        "hero_ghost": "Biz haqimizda",
        "stat_products": "ta mahsulot",
        "stat_delivery": "ta shaharga yetkazish",
        "stat_clients": "mamnun mijoz",
        "card_guarantee": "Rasmiy kafolat",
        "card_delivery": "Shaharlarga yetkazib berish",
        "card_payment": "Olganda to'lash",
        "card_original": "Faqat original",
        "popular_title": "Eng ommabop",
        "all_title": "Tovarlar katalogi",
        "reviews_title": "Mijozlar sharhlari",
        "write_review": "Sharh qoldirish",
        "your_name": "Ismingiz",
        "your_rating": "Baholash",
        "your_review": "Sizning sharhingiz",
        "send_review": "Yuborish",
        "review_submitted": "Rahmat! Sharh tekshiruvga yuborildi",
        "no_reviews": "Hozircha sharhlar yo'q — birinchi bo'ling!",
        "specs_title": "Xususiyatlari",
        "gallery": "Rasmlar",
        "coupon": "Promokod",
        "coupon_ph": "Masalan: WELCOME10",
        "coupon_apply": "Qo'llash",
        "coupon_applied": "Promokod qo'llandi",
        "coupon_invalid": "Promokod topilmadi",
        "coupon_remove": "Olib tashlash",
        "discount": "Chegirma",
        "subtotal": "Mahsulotlar",
        "dashboard": "Dashboard",
        "analytics": "Analitika",
        "stat_orders": "Buyurtmalar",
        "stat_revenue": "Daromad",
        "stat_new": "Yangi",
        "stat_products_admin": "Mahsulotlar",
        "stat_reviews": "Sharhlar",
        "sales_14d": "14 kunlik savdo",
        "top_products": "Eng ko'p sotilganlar",
        "recent_orders": "Oxirgi buyurtmalar",
        "review_approved": "Sharh tasdiqlandi",
        "review_deleted": "Sharh o'chirildi",
        "coupon_saved": "Promokod saqlandi",
        "coupon_deleted": "Promokod o'chirildi",
        "coupons_list": "Promokodlar",
        "code": "Kod",
        "percent": "Chegirma %",
        "active": "Faol",
        "disabled": "O'chirilgan",
        "toggle": "Yoqish/o'chirish",
        "add_coupon": "Promokod qo'shish",
        "specs_label": "Xususiyatlar (har qator: Kalit: qiymat)",
        "gallery_label": "Qo'shimcha rasmlar (bir nechta)",
    },
}

STATUSES = ["new", "processing", "delivered", "cancelled"]


def get_lang():
    lang = session.get("lang", "ru")
    return lang if lang in ("ru", "uz") else "ru"


def t(key):
    return TRANSLATIONS.get(get_lang(), TRANSLATIONS["ru"]).get(key, key)


def money(value):
    v = float(value)
    if v == int(v):
        return f"{int(v):,}".replace(",", " ")
    return f"{v:,.2f}".replace(",", " ").replace(".", ",")


@app.template_filter("money")
def money_filter(value):
    return money(value)


@app.template_filter("product_img")
def product_img_filter(image):
    """Возвращает URL картинки: внешний (http) или локальный /static/img/."""
    if image and str(image).startswith("http"):
        return str(image)
    return url_for("static", filename="img/" + str(image))


def parse_decimal(value):
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------- Общие данные для шаблонов ----------

@app.context_processor
def inject_globals():
    cart_count = sum(session.get("cart", {}).values())
    return {
        "t": t,
        "lang": get_lang(),
        "categories": repo.get_categories(),
        "cart_count": cart_count,
        "request_path": request.path,
        "admin_logged_in": bool(session.get("admin")),
        "statuses": STATUSES,
    }


def cart_items_data():
    """Возвращает список товаров в корзине с ценами и итогом."""
    cart = session.get("cart", {})
    if not cart:
        return [], 0
    ids = [int(i) for i in cart.keys()]
    products = repo.get_products_by_ids(ids)
    by_id = {p["id"]: p for p in products}
    items, total = [], 0
    for pid, qty in cart.items():
        p = by_id.get(int(pid))
        if not p:
            continue
        price = float(p["price"])
        items.append({
            "id": p["id"], "name_ru": p["name_ru"], "name_uz": p["name_uz"],
            "price": price, "qty": qty, "image": p["image"],
            "subtotal": round(price * qty, 2),
        })
        total += price * qty
    return items, round(total, 2)


# ---------- Каталог ----------

@app.route("/")
def index():
    lang = get_lang()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    sort = request.args.get("sort", "popular")
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    filters = {"q": q, "category": category, "sort": sort}
    if min_price:
        filters["min_price"] = min_price
    if max_price:
        filters["max_price"] = max_price

    products = repo.get_products(filters)
    return render_template(
        "index.html",
        products=products,
        active_category=category,
        q=q,
        sort=sort,
        min_price=min_price,
        max_price=max_price,
    )


@app.route("/product/<int:pid>", methods=["GET", "POST"])
def product(pid):
    p = repo.get_product(pid)
    if not p:
        abort(404)

    # Отзыв (POST)
    if request.method == "POST":
        name = request.form.get("review_name", "").strip()
        rating = request.form.get("review_rating", "")
        text = request.form.get("review_text", "").strip()
        if name and rating.isdigit() and text:
            rating = int(rating)
            if 1 <= rating <= 5:
                repo.create_review(pid, name, rating, text)
                flash(t("review_submitted"), "ok")
        return redirect(url_for("product", pid=pid))

    related = repo.get_related(pid, p["category_id"])
    images = repo.get_product_images(pid)
    specs = repo.parse_specs(p.get("specs"))
    reviews = repo.get_reviews(pid, approved_only=True)
    return render_template(
        "product.html", p=p, related=related, images=images,
        specs=specs, reviews=reviews,
    )


# ---------- Корзина ----------

@app.route("/cart")
def cart():
    items, total = cart_items_data()
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add", methods=["POST"])
def cart_add():
    pid = str(request.form.get("product_id", ""))
    if not pid.isdigit():
        abort(400)
    qty = int(request.form.get("qty", 1))
    qty = max(1, min(qty, 99))
    cart = session.get("cart", {})
    cart[pid] = cart.get(pid, 0) + qty
    session["cart"] = cart
    cart_count = sum(cart.values())
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "cart_count": cart_count, "qty": cart[pid]})
    return redirect(request.referrer or url_for("cart"))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    pid = str(request.form.get("product_id", ""))
    qty = int(request.form.get("qty", 1))
    cart = session.get("cart", {})
    if qty <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = min(qty, 99)
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    pid = str(request.form.get("product_id", ""))
    cart = session.get("cart", {})
    cart.pop(pid, None)
    session["cart"] = cart
    return redirect(url_for("cart"))


# ---------- Оформление заказа ----------

def send_telegram_notification(order):
    """Отправляет уведомление о заказе в Telegram (если настроено)."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False
    try:
        items_text = "\n".join(
            f"  • {it['product_name']} × {it['quantity']} — {money(it['price'] * it['quantity'])} UZS"
            for it in repo.get_order_items(order["id"])
        )
        message = (
            f"🛒 <b>НОВЫЙ ЗАКАЗ #{order['id']}</b>\n\n"
            f"👤 {order['customer_name']}\n"
            f"📞 {order['phone']}\n"
            f"🏙 {order['city']}\n"
            f"📍 {order['address']}"
            + (f"\n➕ {order['address2']}" if order.get("address2") else "")
            + f"\n\n{items_text}"
            + (f"\n\n🎟 Промокод: {order['coupon_code']} (−{money(order['discount'])} UZS)" if order.get("discount") else "")
            + f"\n\n🚚 Доставка: {money(order['delivery_price'])} UZS ({order['delivery_minutes']} мин)\n"
            + f"💰 <b>Итого: {money(order['total'])} UZS</b>"
        )
        http_requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": config.TELEGRAM_CHAT_ID, "text": message,
                  "parse_mode": "HTML"},
            timeout=15,
        )
        return True
    except Exception:
        return False


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    lang = get_lang()
    items, total = cart_items_data()
    if not items:
        return redirect(url_for("cart"))

    cities = repo.get_cities()
    form = CheckoutForm()
    form.city.choices = [(str(c["id"]), c["name_ru"] if lang == "ru" else c["name_uz"])
                         for c in cities]

    # Промокод применяем при любом POST/GET показуем текущий
    coupon = None
    coupon_code = ""
    discount = 0
    if form.validate_on_submit():
        coupon_code = form.coupon.data.strip().upper() if form.coupon.data else ""
        if coupon_code:
            coupon = repo.get_coupon(coupon_code)
            if coupon:
                discount = round(total * coupon["discount_percent"] / 100, 2)

        city = repo.get_city(int(form.city.data))
        if not city:
            abort(400)

        city_name = city["name_ru"] if lang == "ru" else city["name_uz"]
        delivery_price = float(city["delivery_price"])
        delivery_minutes = city["delivery_minutes"]
        subtotal = round(total, 2)
        grand_total = round(subtotal - discount + delivery_price, 2)

        order_items = [
            {"name": it["name_ru"] if lang == "ru" else it["name_uz"],
             "price": it["price"], "qty": it["qty"]}
            for it in items
        ]
        order_id = repo.create_order_full(
            customer_name=form.name.data.strip(),
            phone=form.phone.data.strip(),
            city=city_name,
            address=form.address.data.strip(),
            address2=form.address2.data.strip() or None,
            delivery_price=delivery_price,
            delivery_minutes=delivery_minutes,
            subtotal=subtotal,
            discount=discount,
            coupon_code=coupon_code if coupon else None,
            total=grand_total,
            items=order_items,
        )
        # Telegram-уведомление
        order = repo.get_order(order_id)
        if order:
            send_telegram_notification(order)
        session["cart"] = {}
        return redirect(url_for("order_success", order_id=order_id,
                                total=grand_total,
                                delivery_price=delivery_price,
                                delivery_minutes=delivery_minutes,
                                discount=discount,
                                coupon_code=coupon_code if coupon else ""))

    errors = []
    for field in form.errors.values():
        for err in field:
            if isinstance(err, str):
                errors.append(t(err))
    return render_template("checkout.html", items=items, total=total,
                           cities=cities, form=form, errors=errors)


@app.route("/checkout/coupon", methods=["POST"])
def coupon_check():
    """AJAX: проверка промокода, возвращает размер скидки."""
    code = request.form.get("code", "").strip().upper()
    items, total = cart_items_data()
    if not items:
        return jsonify({"ok": False, "error": "cart_empty"})
    coupon = repo.get_coupon(code) if code else None
    if coupon:
        discount = round(total * coupon["discount_percent"] / 100, 2)
        return jsonify({"ok": True, "code": coupon["code"],
                        "percent": coupon["discount_percent"],
                        "discount": discount})
    return jsonify({"ok": False, "error": "invalid"})


@app.route("/order-success")
def order_success():
    order_id = request.args.get("order_id")
    total = request.args.get("total")
    delivery_price = request.args.get("delivery_price")
    delivery_minutes = request.args.get("delivery_minutes")
    discount = request.args.get("discount", "0")
    coupon_code = request.args.get("coupon_code", "")
    return render_template(
        "success.html",
        order_id=order_id, total=total,
        delivery_price=delivery_price, delivery_minutes=delivery_minutes,
        discount=discount, coupon_code=coupon_code,
    )


@app.route("/set-lang/<lang>")
def set_lang(lang):
    if lang in ("ru", "uz"):
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


# ---------- Админ-панель ----------

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM admins WHERE username=%s", (form.username.data.strip(),))
        admin = cur.fetchone()
        cur.close()
        conn.close()
        if admin and check_password_hash(admin[2], form.password.data):
            session["admin"] = admin[1]
            return redirect(url_for("admin_orders"))
        flash(t("invalid_credentials"), "error")
    return render_template("admin/login.html", form=form)


@app.route("/admin/logout")
def logout():
    session.pop("admin", None)
    flash(t("logged_out"), "ok")
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_panel():
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    status_filter = request.args.get("status", "")
    orders = repo.get_orders(status_filter or None)
    orders_list = []
    for o in orders:
        order_items = repo.get_order_items(o["id"])
        orders_list.append({"order": o, "order_items": order_items})
    return render_template("admin/orders.html", orders=orders_list,
                           status_filter=status_filter)


@app.route("/admin/orders/<int:oid>/status", methods=["POST"])
@admin_required
def admin_order_status(oid):
    status = request.form.get("status", "")
    if status in STATUSES:
        repo.update_order_status(oid, status)
        flash(t("status_updated"), "ok")
    return redirect(url_for("admin_orders"))


# --- Товары ---

import requests as http_requests

def save_product_image(form):
    """Загружает фото в облако (uguu.se), возвращает URL или None."""
    file = form.image_file.data
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        abort(400, "Недопустимый формат изображения")
    try:
        resp = http_requests.post(
            "https://uguu.se/upload.php",
            files={"files[]": (file.filename, file.stream, f"image/{ext[1:]}")},
            timeout=60,
        )
        data = resp.json()
        url = data["files"][0]["url"]
        if url:
            return url
    except Exception:
        pass
    abort(500, "Не удалось загрузить изображение")


def save_gallery_images(form):
    """Загружает все файлы галереи, возвращает список URL."""
    files = form.gallery_files.data if hasattr(form, "gallery_files") else None
    urls = []
    if not files:
        return urls
    for f in files:
        if not f or not f.filename:
            continue
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
            continue
        try:
            resp = http_requests.post(
                "https://uguu.se/upload.php",
                files={"files[]": (f.filename, f.stream, f"image/{ext[1:]}")},
                timeout=60,
            )
            data = resp.json()
            url = data["files"][0]["url"]
            if url:
                urls.append(url)
        except Exception:
            continue
    return urls


def parse_specs_text(text):
    """Парсит specs из текста: строки 'Ключ: значение'."""
    result = []
    if not text:
        return result
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            result.append([k.strip(), v.strip()])
        else:
            result.append([line, ""])
    return result


@app.route("/admin/products")
@admin_required
def admin_products():
    products = repo.get_products({"sort": "popular"})
    return render_template("admin/products.html", products=products)


@app.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    form = ProductForm()
    form.category_id.choices = [
        (str(c["id"]), c["name_ru"]) for c in repo.get_categories()
    ]
    if form.validate_on_submit():
        image_name = save_product_image(form) or form.image.data.strip() or "no-image.png"
        specs_json = json.dumps(parse_specs_text(form.specs.data), ensure_ascii=False)
        result = repo.create_product({
            "category_id": int(form.category_id.data),
            "name_ru": form.name_ru.data.strip(),
            "name_uz": form.name_uz.data.strip(),
            "description_ru": form.description_ru.data.strip(),
            "description_uz": form.description_uz.data.strip(),
            "price": form.price.data,
            "old_price": form.old_price.data,
            "stock": form.stock.data,
            "image": image_name,
            "rating": form.rating.data or 5.0,
            "reviews": form.reviews.data or 0,
            "specs_json": specs_json,
        })
        if result and result.get("id"):
            gallery = save_gallery_images(form)
            for pos, url in enumerate(gallery):
                repo.add_product_image(result["id"], url, pos)
        flash(t("product_saved"), "ok")
        return redirect(url_for("admin_products"))
    return render_template("admin/product_form.html", form=form,
                           categories=repo.get_categories(), product=None)


@app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(pid):
    p = repo.get_product(pid)
    if not p:
        abort(404)
    form = ProductForm()
    form.category_id.choices = [
        (str(c["id"]), c["name_ru"]) for c in repo.get_categories()
    ]
    if form.validate_on_submit():
        image_name = save_product_image(form) or p["image"]
        specs_json = json.dumps(parse_specs_text(form.specs.data), ensure_ascii=False)
        repo.update_product(pid, {
            "category_id": int(form.category_id.data),
            "name_ru": form.name_ru.data.strip(),
            "name_uz": form.name_uz.data.strip(),
            "description_ru": form.description_ru.data.strip(),
            "description_uz": form.description_uz.data.strip(),
            "price": form.price.data,
            "old_price": form.old_price.data,
            "stock": form.stock.data,
            "image": image_name,
            "rating": form.rating.data or 5.0,
            "reviews": form.reviews.data or 0,
            "specs_json": specs_json,
        })
        gallery = save_gallery_images(form)
        if gallery:
            repo.clear_product_images(pid)
            for pos, url in enumerate(gallery):
                repo.add_product_image(pid, url, pos)
        flash(t("product_saved"), "ok")
        return redirect(url_for("admin_products"))
    if not form.is_submitted():
        form.category_id.data = str(p["category_id"])
        form.name_ru.data = p["name_ru"]
        form.name_uz.data = p["name_uz"]
        form.description_ru.data = p["description_ru"]
        form.description_uz.data = p["description_uz"]
        form.price.data = p["price"]
        form.old_price.data = p["old_price"]
        form.stock.data = p["stock"]
        form.image.data = p["image"]
        form.rating.data = p["rating"]
        form.reviews.data = p["reviews"]
        specs = repo.parse_specs(p.get("specs"))
        form.specs.data = "\n".join(f"{k}: {v}" for k, v in specs)
    images = repo.get_product_images(pid)
    return render_template("admin/product_form.html", form=form,
                           categories=repo.get_categories(), product=p,
                           images=images)


@app.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_product_delete(pid):
    repo.delete_product(pid)
    flash(t("product_deleted"), "ok")
    return redirect(url_for("admin_products"))


# --- Дашборд / аналитика ---

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    summary = repo.analytics_summary()
    by_status = repo.analytics_orders_by_status()
    sales = repo.analytics_sales_by_day(14)
    top = repo.analytics_top_products(5)
    recent = repo.analytics_recent_orders(8)
    status_map = {row["status"]: row["count"] for row in by_status}
    return render_template(
        "admin/dashboard.html",
        summary=summary,
        status_map=status_map,
        sales=sales,
        top=top,
        recent=recent,
    )


# --- Отзывы ---

@app.route("/admin/reviews")
@admin_required
def admin_reviews():
    status = request.args.get("status", "")
    reviews = repo.get_all_reviews(status or None)
    return render_template("admin/reviews.html", reviews=reviews,
                           status_filter=status)


@app.route("/admin/reviews/<int:rid>/approve", methods=["POST"])
@admin_required
def admin_review_approve(rid):
    review = db.fetch_one("SELECT * FROM reviews WHERE id=%s", (rid,))
    if review:
        repo.approve_review(rid, True)
        repo.recalc_product_rating(review["product_id"])
        flash(t("review_approved"), "ok")
    return redirect(url_for("admin_reviews"))


@app.route("/admin/reviews/<int:rid>/delete", methods=["POST"])
@admin_required
def admin_review_delete(rid):
    review = db.fetch_one("SELECT * FROM reviews WHERE id=%s", (rid,))
    if review:
        repo.delete_review(rid)
        repo.recalc_product_rating(review["product_id"])
        flash(t("review_deleted"), "ok")
    return redirect(url_for("admin_reviews"))


# --- Промокоды ---

@app.route("/admin/coupons", methods=["GET", "POST"])
@admin_required
def admin_coupons():
    form = CouponForm()
    if form.validate_on_submit():
        repo.create_coupon(form.code.data, form.discount_percent.data)
        flash(t("coupon_saved"), "ok")
        return redirect(url_for("admin_coupons"))
    coupons = repo.get_coupons()
    return render_template("admin/coupons.html", form=form, coupons=coupons)


@app.route("/admin/coupons/<int:cid>/toggle", methods=["POST"])
@admin_required
def admin_coupon_toggle(cid):
    coupon = db.fetch_one("SELECT * FROM coupons WHERE id=%s", (cid,))
    if coupon:
        repo.update_coupon(cid, coupon["code"], coupon["discount_percent"],
                           not coupon["active"])
        flash(t("coupon_saved"), "ok")
    return redirect(url_for("admin_coupons"))


@app.route("/admin/coupons/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_coupon_delete(cid):
    repo.delete_coupon(cid)
    flash(t("coupon_deleted"), "ok")
    return redirect(url_for("admin_coupons"))


# --- Категории ---

@app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        repo.create_category(
            form.slug.data.strip(), form.name_ru.data.strip(),
            form.name_uz.data.strip(), form.icon.data.strip(),
        )
        flash(t("category_saved"), "ok")
        return redirect(url_for("admin_categories"))
    categories = repo.get_categories()
    return render_template("admin/categories.html", form=form,
                           categories=categories)


@app.route("/admin/categories/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_category_delete(cid):
    repo.delete_category(cid)
    flash(t("category_deleted"), "ok")
    return redirect(url_for("admin_categories"))


# --- Города (доставка) ---

@app.route("/admin/cities", methods=["GET", "POST"])
@admin_required
def admin_cities():
    form = CityForm()
    if form.validate_on_submit():
        repo.create_city(
            form.name_ru.data.strip(), form.name_uz.data.strip(),
            form.delivery_price.data, form.delivery_minutes.data,
        )
        flash(t("city_saved"), "ok")
        return redirect(url_for("admin_cities"))
    cities = repo.get_cities()
    return render_template("admin/cities.html", form=form, cities=cities)


@app.route("/admin/cities/<int:cid>/delete", methods=["POST"])
@admin_required
def admin_city_delete(cid):
    repo.delete_city(cid)
    flash(t("city_deleted"), "ok")
    return redirect(url_for("admin_cities"))


# ---------- Ошибки ----------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)