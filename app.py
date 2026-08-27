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
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from flask import (Flask, render_template, request, redirect, url_for,
                   session, abort, flash, jsonify)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import config
import database as db
import repository as repo
from database import get_conn
from forms import (csrf, CheckoutForm, LoginForm, ProductForm,
                   CategoryForm, CityForm, CouponForm, AdminForm, AdminEditForm)

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["WTF_CSRF_TIME_LIMIT"] = None
app.config["WTF_CSRF_SSL_STRICT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30  # 30 дней
csrf.init_app(app)


@app.before_request
def make_session_permanent():
    session.permanent = True

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
        "status_shipping": "Доставляется",
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
        "email_invalid": "Некорректный email",
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
        "no_permission": "Недостаточно прав для этого раздела",
        "admins_title": "Администраторы",
        "add_admin": "Добавить администратора",
        "edit_admin": "Редактировать администратора",
        "role": "Роль",
        "role_superadmin": "Генеральный",
        "role_manager": "Менеджер",
        "permissions_label": "Права доступа",
        "all_permissions": "Все права (генеральный)",
        "admin_exists": "Администратор с таким логином уже существует",
        "admin_saved": "Администратор сохранён",
        "admin_deleted": "Администратор удалён",
        "admin_cannot_delete_self": "Нельзя удалить самого себя",
        "created": "Создан",
        "select_permissions": "Отметьте разделы, к которым дать доступ",
        "login_admin": "Логин",
        "optional_field": "необязательно",
        "password_keep": "Оставьте пустым, чтобы не менять",
        "wishlist": "Избранное",
        "wishlist_title": "Избранное",
        "wishlist_empty": "В избранном пока пусто",
        "wishlist_empty_hint": "Нажмите на сердечко у товара, чтобы сохранить его",
        "add_wish": "В избранное",
        "remove_wish": "Убрать",
        "wish_added": "Добавлено в избранное",
        "wish_removed": "Убрано из избранного",
        "track": "Отследить заказ",
        "track_title": "Отслеживание заказа",
        "track_hint": "Введите номер заказа, чтобы узнать его статус",
        "track_ph": "Например: 123",
        "track_btn": "Найти заказ",
        "track_invalid": "Введите номер заказа (цифры)",
        "track_not_found": "Заказ с таким номером не найден",
        "track_order_title": "Заказ #",
        "order_details": "Детали заказа",
        "order_placed": "Заказ оформлен",
        "order_processing": "В обработке",
        "order_delivered": "Доставлен",
        "order_cancelled": "Отменён",
        "avg_check": "Средний чек",
        "sales_monthly": "Продажи по месяцам",
        "export_orders": "Экспорт заказов (CSV)",
        "about": "О проекте",
        "about_title": "О проекте TechStore",
        "about_sub": "Полноценный интернет-магазин техники — портфолио backend-разработчика",
        "about_what_title": "Что это",
        "about_what_text": "TechStore — это профессиональный интернет-магазин электроники с настоящим бэкендом. Проект создан как портфолио: он показывает, как устроен реальный e-commerce изнутри — от базы данных до витрины и админ-панели.",
        "about_stack_title": "Технологии",
        "about_stack_text": "Проект построен на Python-стеке с чётким разделением на слои: конфигурация, доступ к данным, SQL-запросы, формы и роуты.",
        "stack_flask": "Flask 3.1 — веб-фреймворк",
        "stack_postgres": "PostgreSQL — база данных (Neon, облако)",
        "stack_psycopg": "psycopg2 — драйвер для работы с БД",
        "stack_wtf": "Flask-WTF / WTForms — формы и валидация",
        "stack_cloud": "Render — хостинг, uguu.se — хранение фото",
        "stack_front": "HTML, CSS, JavaScript — адаптивный интерфейс",
        "stack_git": "Git + GitHub — версионирование",
        "about_features_title": "Возможности",
        "about_features_text": "Сайт делает всё, что умеет настоящий магазин:",
        "feat_catalog": "Каталог с поиском, фильтрами, сортировкой и пагинацией",
        "feat_cart": "Корзина с AJAX-добавлением без перезагрузки",
        "feat_order": "Оформление заказа: город, доставка, адрес, промокоды",
        "feat_track": "Отслеживание статуса заказа по номеру",
        "feat_wishlist": "Избранное с сохранением в сессии",
        "feat_reviews": "Отзывы покупателей с рейтингом",
        "feat_gallery": "Галерея фото и характеристики товаров",
        "feat_admin": "Админ-панель с ролями и правами доступа",
        "feat_analytics": "Аналитика: графики продаж, средний чек, экспорт CSV",
        "feat_telegram": "Уведомления о заказах в Telegram",
        "feat_i18n": "Двуязычный интерфейс RU / UZ",
        "feat_theme": "Тёмная тема и мобильная версия",
        "about_author_title": "Автор",
        "about_author_text": "Проект создан Жахангиром — бэкенд-разработчиком из Ташкента. Python, PostgreSQL, Flask — мой стек.",
        "about_note": "Это портфолио-проект. Все товары и заказы — демонстрационные.",
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
        "status_shipping": "Yetkazilmoqda",
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
        "email_invalid": "Email noto'g'ri",
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
        "no_permission": "Ushbu bo'lim uchun huquqlar yetarli emas",
        "admins_title": "Administratorlar",
        "add_admin": "Administrator qo'shish",
        "edit_admin": "Administratorni tahrirlash",
        "role": "Rol",
        "role_superadmin": "Bosh administrator",
        "role_manager": "Menejer",
        "permissions_label": "Kirish huquqlari",
        "all_permissions": "Barcha huquqlar (bosh administrator)",
        "admin_exists": "Bunday loginli administrator allaqachon mavjud",
        "admin_saved": "Administrator saqlandi",
        "admin_deleted": "Administrator o'chirildi",
        "admin_cannot_delete_self": "O'zingizni o'chirib bo'lmaydi",
        "created": "Yaratilgan",
        "select_permissions": "Kirish beriladigan bo'limlarni belgilang",
        "login_admin": "Login",
        "optional_field": "ixtiyoriy",
        "password_keep": "O'zgartirmaslik uchun bo'sh qoldiring",
        "wishlist": "Sevimlilar",
        "wishlist_title": "Sevimlilar",
        "wishlist_empty": "Sevimlilar bo'sh",
        "wishlist_empty_hint": "Mahsulotdagi yurakchani bosing va saqlang",
        "add_wish": "Sevimlilarga",
        "remove_wish": "Olib tashlash",
        "wish_added": "Sevimlilarga qo'shildi",
        "wish_removed": "Sevimlilardan olib tashlandi",
        "track": "Buyurtmani kuzatish",
        "track_title": "Buyurtmani kuzatish",
        "track_hint": "Holatini bilish uchun buyurtma raqamini kiriting",
        "track_ph": "Masalan: 123",
        "track_btn": "Buyurtmani topish",
        "track_invalid": "Buyurtma raqamini kiriting (raqamlar)",
        "track_not_found": "Bunday raqamli buyurtma topilmadi",
        "track_order_title": "Buyurtma #",
        "order_details": "Buyurtma tafsilotlari",
        "order_placed": "Buyurtma qabul qilindi",
        "order_processing": "Jarayonda",
        "order_delivered": "Yetkazildi",
        "order_cancelled": "Bekor qilindi",
        "avg_check": "O'rtacha chek",
        "sales_monthly": "Oylik savdo",
        "export_orders": "Buyurtmalar eksporti (CSV)",
        "about": "Loyiha haqida",
        "about_title": "TechStore loyihasi haqida",
        "about_sub": "To'liq texnika internet-do'koni — backend dasturchi portfolio",
        "about_what_title": "Bu nima",
        "about_what_text": "TechStore — haqiqiy backendga ega professional elektronika internet-do'koni. Loyiha portfolio sifatida yaratilgan: u haqiqiy e-commerce ichkaridan qanday tuzilganini ko'rsatadi — bazadan tortib vitrina va admin panelgacha.",
        "about_stack_title": "Texnologiyalar",
        "about_stack_text": "Loyiha Python-stekda qat'iy qatlamlarga bo'lingan: konfiguratsiya, ma'lumotlarga kirish, SQL so'rovlar, formalar va routlar.",
        "stack_flask": "Flask 3.1 — veb-framework",
        "stack_postgres": "PostgreSQL — ma'lumotlar bazasi (Neon, bulut)",
        "stack_psycopg": "psycopg2 — ma'lumotlar bazasi bilan ishlash",
        "stack_wtf": "Flask-WTF / WTForms — formalar va validatsiya",
        "stack_cloud": "Render — hosting, uguu.se — rasm saqlash",
        "stack_front": "HTML, CSS, JavaScript — adaptiv interfeys",
        "stack_git": "Git + GitHub — versiyalash",
        "about_features_title": "Imkoniyatlar",
        "about_features_text": "Sayt haqiqiy do'kon qila oladigan hamma narsani qiladi:",
        "feat_catalog": "Qidiruv, filtrlar, saralash va paginatsiyali katalog",
        "feat_cart": "AJAX bilan sahifa qayta yuklanmasdan savat",
        "feat_order": "Buyurtma rasmiylashtirish: shahar, yetkazib berish, manzil, promokodlar",
        "feat_track": "Buyurtma holatini raqam bo'yicha kuzatish",
        "feat_wishlist": "Sevimlilarni sessiyada saqlash",
        "feat_reviews": "Mijozlar sharhlari va reyting",
        "feat_gallery": "Rasmlar galereyasi va mahsulot xususiyatlari",
        "feat_admin": "Rollar va kirish huquqlari bilan admin panel",
        "feat_analytics": "Analitika: savdo grafiklari, o'rtacha chek, CSV eksport",
        "feat_telegram": "Buyurtmalar haqida Telegram xabarlari",
        "feat_i18n": "Ikki tilli interfeys RU / UZ",
        "feat_theme": "Qorong'u mavzu va mobil versiya",
        "about_author_title": "Muallif",
        "about_author_text": "Loyiha Toshkentlik backend dasturchi Jahongir tomonidan yaratilgan. Python, PostgreSQL, Flask — mening stekim.",
        "about_note": "Bu portfolio-loyiha. Barcha tovarlar va buyurtmalar — namoyish uchun.",
    },
}

STATUSES = ["new", "processing", "shipping", "delivered", "cancelled"]


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


ICONS = {
    "cart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><circle cx="9" cy="21" r="1.6"/><circle cx="20" cy="21" r="1.6"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
    "bookmark": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>',
    "bookmark-fill": '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
    "lock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "box": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><polyline points="20 6 9 17 4 12"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "money": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    "headphones": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>',
    "diamond": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M6 3h12l4 6-10 13L2 9z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "ticket": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M3 6h18v4a2 2 0 0 0 0 4v4H3v-4a2 2 0 0 0 0-4z"/><line x1="13" y1="6" x2="13" y2="18"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    "city": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/><line x1="9" y1="9" x2="9" y2="9.01"/><line x1="9" y1="12" x2="9" y2="12.01"/><line x1="9" y1="15" x2="9" y2="15.01"/></svg>',
    "settings": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "bag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x1="21" y1="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
    "chart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "tag": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M20.59 13.41 11 3.82A2 2 0 0 0 9.59 3H4a1 1 0 0 0-1 1v5.59A2 2 0 0 0 3.82 11l9.59 9.59a2 2 0 0 0 2.83 0l4.35-4.35a2 2 0 0 0 0-2.83z"/><circle cx="7.5" cy="7.5" r=".5"/></svg>',
    "list": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
    "database": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "cloud": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>',
    "palette": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.72-.68 1.87-1.6a1.8 1.8 0 0 0-.53-1.55A1.8 1.8 0 0 1 13 17c1.66 0 3-1.34 3-3 0-.55-.45-1-1-1h-1.2c-.8 0-1.4-.7-1.35-1.5.05-.7.62-1.22 1.3-1.44.46-.15.75-.6.75-1.06C15.5 8.02 13.95 6 12 6z"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
    "edit": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4z"/></svg>',
    "download": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    "python": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M12 9H7a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h5"/><path d="M12 15h5a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2h-5"/><path d="M9 2v5M15 17v5"/></svg>',
    "plug": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M9 2v6M15 2v6"/><path d="M7 8h10v4a5 5 0 0 1-10 0z"/><line x1="12" y1="17" x2="12" y2="22"/></svg>',
    "git": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><path d="M6 9v6"/><path d="M9 6h6a3 3 0 0 1 3 3v0"/><path d="M18 9v9"/></svg>',
    "bulb": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5.76.76 1.23 1.52 1.41 2.5z"/></svg>',
    "photo": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "paper": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "alert": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "crown": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="m2 6 5 4 5-8 5 8 5-4-2 13H4z"/></svg>',
    "user": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    "plus": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="22" height="22"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
}

CATEGORY_ICONS = {
    "phones": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" width="28" height="28"><rect x="7" y="2" width="10" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>',
    "laptops": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" width="28" height="28"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M2 20h20"/></svg>',
    "tablets": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" width="28" height="28"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>',
    "tv": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" width="28" height="28"><rect x="2" y="7" width="20" height="13" rx="2"/><polyline points="17 2 12 7 7 2"/></svg>',
    "accessories": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" width="28" height="28"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>',
}


@app.template_filter("icon")
def icon_filter(name):
    return ICONS.get(name, "")


@app.template_filter("cat_icon")
def cat_icon_filter(slug):
    return CATEGORY_ICONS.get(str(slug), ICONS["box"])


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


PERMISSIONS = [
    ("orders", "📦 " + "Заказы"),
    ("products", "🏷️ " + "Товары"),
    ("categories", "🗂️ " + "Категории"),
    ("cities", "🚚 " + "Доставка"),
    ("reviews", "⭐ " + "Отзывы"),
    ("coupons", "🎟️ " + "Промокоды"),
    ("dashboard", "📊 " + "Аналитика"),
    ("admins", "👥 " + "Администраторы"),
]

PERMISSION_KEYS = [p[0] for p in PERMISSIONS]


def permission_required(permission):
    """Доступ только для админов с нужным правом (или superadmin)."""
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            admin = session.get("admin")
            if not admin:
                return redirect(url_for("login"))
            role = admin.get("role")
            perms = admin.get("permissions", [])
            if role != "superadmin" and permission not in perms:
                flash(t("no_permission"), "error")
                return redirect(url_for("admin_panel"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def current_admin():
    """Объект текущего админа с проверкой в БД (актуальные права)."""
    admin_id = session.get("admin_id")
    if not admin_id:
        return None
    return repo.get_admin_by_id(admin_id)


# ---------- Общие данные для шаблонов ----------

@app.context_processor
def inject_globals():
    cart_count = sum(session.get("cart", {}).values())
    wish_count = len(session.get("wishlist", {}))
    admin = session.get("admin")
    return {
        "t": t,
        "lang": get_lang(),
        "categories": repo.get_categories(),
        "icon": icon_filter,
        "cat_icon": cat_icon_filter,
        "cart_count": cart_count,
        "wish_count": wish_count,
        "request_path": request.path,
        "admin_logged_in": bool(admin),
        "admin_username": (admin or {}).get("username", ""),
        "admin_role": (admin or {}).get("role", ""),
        "admin_is_super": bool(admin and admin.get("role") == "superadmin"),
        "admin_permissions": (admin or {}).get("permissions", []),
        "statuses": STATUSES,
        "permissions": PERMISSIONS,
    }


def _user_id():
    """ID залогиненного пользователя (клиента) или None."""
    return session.get("user_id")


def _get_cart_store():
    """Возвращает словарь {pid: qty} из БД (если залогинен) или сессии."""
    uid = _user_id()
    if uid:
        return repo.get_user_items(uid, "cart")
    return session.get("cart", {})


def _save_cart_store(cart):
    """Сохраняет корзину в БД (если залогинен) или сессию."""
    uid = _user_id()
    if uid:
        repo.clear_user_items(uid, "cart")
        for pid, qty in cart.items():
            repo.set_user_item(uid, int(pid), "cart", qty)
    else:
        session["cart"] = cart


def _get_wish_store():
    uid = _user_id()
    if uid:
        return set(repo.get_user_items(uid, "wish").keys())
    return set(session.get("wishlist", {}))


def _save_wish_store(wish):
    uid = _user_id()
    if uid:
        repo.clear_user_items(uid, "wish")
        for pid in wish:
            repo.set_user_item(uid, int(pid), "wish", 1)
    else:
        session["wishlist"] = {str(pid): True for pid in wish}


def _get_compare_store():
    uid = _user_id()
    if uid:
        return set(repo.get_user_items(uid, "compare").keys())
    return set(session.get("compare", []))


def _merge_guest_data(uid):
    """Переносит корзину/избранное/сравнение из сессии в БД при входе."""
    cart = session.get("cart", {})
    if cart:
        for pid, qty in cart.items():
            repo.set_user_item(uid, int(pid), "cart", qty)
    wish = session.get("wishlist", {})
    if wish:
        for pid in wish:
            repo.set_user_item(uid, int(pid), "wish", 1)
    compare = session.get("compare", [])
    if compare:
        for pid in compare:
            repo.set_user_item(uid, int(pid), "compare", 1)
    session.pop("cart", None)
    session.pop("wishlist", None)
    session.pop("compare", None)


def _save_compare_store(compare):
    uid = _user_id()
    if uid:
        repo.clear_user_items(uid, "compare")
        for pid in compare:
            repo.set_user_item(uid, int(pid), "compare", 1)
    else:
        session["compare"] = list(compare)


def cart_items_data():
    """Возвращает список товаров в корзине с ценами и итогом."""
    cart = _get_cart_store()
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

# @app.route("/")
def index():
    lang = get_lang()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    sort = request.args.get("sort", "popular")
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    page = request.args.get("page", 1, type=int)

    filters = {"q": q, "category": category, "sort": sort, "page": page, "per_page": 12}
    if min_price:
        filters["min_price"] = min_price
    if max_price:
        filters["max_price"] = max_price

    products, total, page, per_page = repo.get_products(filters)
    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template(
        "index.html",
        products=products,
        active_category=category,
        q=q,
        sort=sort,
        min_price=min_price,
        max_price=max_price,
        page=page,
        total_pages=total_pages,
        total=total,
    )


# @app.route("/product/<int:pid>", methods=["GET", "POST"])
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

# @app.route("/cart")
def cart():
    items, total = cart_items_data()
    return render_template("cart.html", items=items, total=total)


# ---------- Избранное ----------

# @app.route("/wishlist")
def wishlist():
    wish = session.get("wishlist", {})
    products = []
    if wish:
        ids = [int(i) for i in wish.keys()]
        products = repo.get_products_by_ids(ids)
    return render_template("wishlist.html", products=products)


# @app.route("/wishlist/toggle", methods=["POST"])
def wishlist_toggle():
    pid = str(request.form.get("product_id", ""))
    if not pid.isdigit():
        abort(400)
    wish = session.get("wishlist", {})
    if pid in wish:
        wish.pop(pid)
        added = False
    else:
        wish[pid] = True
        added = True
    session["wishlist"] = wish
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "added": added, "wish_count": len(wish)})
    return redirect(request.referrer or url_for("wishlist"))


# @app.route("/cart/add", methods=["POST"])
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


# @app.route("/cart/update", methods=["POST"])
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


# @app.route("/cart/remove", methods=["POST"])
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
            f"📞 {order['phone']}"
            + (f"\n📧 {order['email']}" if order.get("email") else "")
            + f"\n🏙 {order['city']}\n"
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


def send_order_email(order):
    """Отправляет подтверждение заказа на email клиента (если настроен SMTP)."""
    email = order.get("email")
    if not email or not config.SMTP_HOST:
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        items_text = "\n".join(
            f"- {it['product_name']} x {it['quantity']} = {money(it['price'] * it['quantity'])} UZS"
            for it in repo.get_order_items(order["id"])
        )
        body = (
            f"Спасибо за заказ #{order['id']} в TechStore!\n\n"
            f"Состав заказа:\n{items_text}\n"
            + (f"Промокод {order['coupon_code']}: -{money(order['discount'])} UZS\n" if order.get("discount") else "")
            + f"\nДоставка: {money(order['delivery_price'])} UZS ({order['delivery_minutes']} мин)\n"
            + f"ИТОГО: {money(order['total'])} UZS\n\n"
            + "Оплата при получении. Мы свяжемся с вами по телефону.\n"
            + f"Отследить заказ: {request.host_url}track/{order['id']}"
        )
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = Header(f"Ваш заказ #{order['id']} в TechStore", "utf-8")
        msg["From"] = config.SMTP_FROM
        msg["To"] = email
        with smtplib.SMTP(config.SMTP_HOST, int(config.SMTP_PORT or 587), timeout=20) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.SMTP_FROM, [email], msg.as_string())
        return True
    except Exception:
        return False


# @app.route("/checkout", methods=["GET", "POST"])
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
            email=(form.email.data or "").strip() or None,
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
            send_order_email(order)
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


# @app.route("/checkout/coupon", methods=["POST"])
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


# @app.route("/order-success")
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


# ---------- Отслеживание заказа ----------

# @app.route("/track", methods=["GET", "POST"])
def track():
    """Поиск заказа по номеру."""
    if request.method == "POST":
        oid = request.form.get("order_id", "").strip()
        if oid.isdigit():
            return redirect(url_for("track_order", oid=int(oid)))
        flash(t("track_invalid"), "error")
    return render_template("track.html")


# @app.route("/track/<int:oid>")
def track_order(oid):
    order = repo.get_order(oid)
    if not order:
        flash(t("track_not_found"), "error")
        return redirect(url_for("track"))
    items = repo.get_order_items(oid)
    return render_template("track_order.html", order=order, items=items)


# @app.route("/about")
def about():
    return render_template("about.html")


# @app.route("/set-lang/<lang>")
def set_lang(lang):
    if lang in ("ru", "uz"):
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


# ---------- Админ-панель ----------

def first_allowed_section(role, perms):
    """Первый раздел админки, доступный пользователю."""
    order = ["orders", "products", "reviews", "coupons", "categories", "cities", "dashboard"]
    for key in order:
        if role == "superadmin" or key in perms:
            return {
                "orders": "admin_orders",
                "products": "admin_products",
                "reviews": "admin_reviews",
                "coupons": "admin_coupons",
                "categories": "admin_categories",
                "cities": "admin_cities",
                "dashboard": "admin_dashboard",
            }[key]
    return "admin_dashboard"


# @app.route("/admin/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = repo.get_admin_by_username(form.username.data.strip())
        if admin and check_password_hash(admin["password_hash"], form.password.data):
            perms = admin.get("permissions") or []
            if isinstance(perms, str):
                import json as _json
                try:
                    perms = _json.loads(perms)
                except Exception:
                    perms = []
            session["admin"] = {
                "id": admin["id"],
                "username": admin["username"],
                "role": admin["role"],
                "permissions": perms,
            }
            return redirect(url_for(first_allowed_section(admin["role"], perms)))
        flash(t("invalid_credentials"), "error")
    return render_template("admin/login.html", form=form)


# @app.route("/admin/logout")
def logout():
    session.pop("admin", None)
    session.pop("admin_id", None)
    flash(t("logged_out"), "ok")
    return redirect(url_for("index"))


# @app.route("/admin")
@admin_required
def admin_panel():
    admin = session.get("admin")
    return redirect(url_for(first_allowed_section(
        admin.get("role", ""), admin.get("permissions", []))))


# @app.route("/admin/orders")
@admin_required
@permission_required("orders")
def admin_orders():
    status_filter = request.args.get("status", "")
    orders = repo.get_orders(status_filter or None)
    orders_list = []
    for o in orders:
        order_items = repo.get_order_items(o["id"])
        orders_list.append({"order": o, "order_items": order_items})
    return render_template("admin/orders.html", orders=orders_list,
                           status_filter=status_filter)


# @app.route("/admin/orders/<int:oid>/status", methods=["POST"])
@admin_required
@permission_required("orders")
def admin_order_status(oid):
    status = request.form.get("status", "")
    if status in STATUSES:
        repo.update_order_status(oid, status)
        flash(t("status_updated"), "ok")
    return redirect(url_for("admin_orders"))


# @app.route("/admin/orders/export")
@admin_required
@permission_required("orders")
def admin_orders_export():
    """Экспорт заказов в CSV (для Excel/бухгалтерии)."""
    import csv as _csv
    import io as _io
    orders = repo.get_orders()
    buf = _io.StringIO()
    writer = _csv.writer(buf)
    writer.writerow(["ID", "Дата", "Клиент", "Телефон", "Email", "Город", "Адрес",
                     "Доставка", "Промокод", "Скидка", "Итого", "Статус"])
    for o in orders:
        writer.writerow([
            o["id"], o["created_at"].strftime("%d.%m.%Y %H:%M"),
            o["customer_name"], o["phone"], o.get("email") or "", o["city"], o["address"],
            o["delivery_price"], o.get("coupon_code") or "",
            o.get("discount") or 0, o["total"], o["status"],
        ])
    csv_data = buf.getvalue()
    response = app.response_class(
        "\ufeff" + csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )
    return response


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


# @app.route("/admin/products")
@admin_required
@permission_required("products")
def admin_products():
    products, _, _, _ = repo.get_products({"sort": "popular", "per_page": 999})
    return render_template("admin/products.html", products=products)


# @app.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
@permission_required("products")
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


# @app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
@permission_required("products")
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


# @app.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
@permission_required("products")
def admin_product_delete(pid):
    repo.delete_product(pid)
    flash(t("product_deleted"), "ok")
    return redirect(url_for("admin_products"))


# --- Дашборд / аналитика ---

# @app.route("/admin/dashboard")
@admin_required
@permission_required("dashboard")
def admin_dashboard():
    summary = repo.analytics_summary()
    by_status = repo.analytics_orders_by_status()
    sales = repo.analytics_sales_by_day(14)
    sales_months = repo.analytics_sales_by_month(6)
    top = repo.analytics_top_products(5)
    recent = repo.analytics_recent_orders(8)
    status_map = {row["status"]: row["count"] for row in by_status}
    return render_template(
        "admin/dashboard.html",
        summary=summary,
        status_map=status_map,
        sales=sales,
        sales_months=sales_months,
        top=top,
        recent=recent,
    )


# --- Отзывы ---

# @app.route("/admin/reviews")
@admin_required
@permission_required("reviews")
def admin_reviews():
    reviews = repo.get_all_reviews()
    return render_template("admin/reviews.html", reviews=reviews)


# @app.route("/admin/reviews/<int:rid>/delete", methods=["POST"])
@admin_required
@permission_required("reviews")
def admin_review_delete(rid):
    review = db.fetch_one("SELECT * FROM reviews WHERE id=%s", (rid,))
    if review:
        repo.delete_review(rid)
        repo.recalc_product_rating(review["product_id"])
        flash(t("review_deleted"), "ok")
    return redirect(url_for("admin_reviews"))


# --- Промокоды ---

# @app.route("/admin/coupons", methods=["GET", "POST"])
@admin_required
@permission_required("coupons")
def admin_coupons():
    form = CouponForm()
    if form.validate_on_submit():
        repo.create_coupon(form.code.data, form.discount_percent.data)
        flash(t("coupon_saved"), "ok")
        return redirect(url_for("admin_coupons"))
    coupons = repo.get_coupons()
    return render_template("admin/coupons.html", form=form, coupons=coupons)


# @app.route("/admin/coupons/<int:cid>/toggle", methods=["POST"])
@admin_required
@permission_required("coupons")
def admin_coupon_toggle(cid):
    coupon = db.fetch_one("SELECT * FROM coupons WHERE id=%s", (cid,))
    if coupon:
        repo.update_coupon(cid, coupon["code"], coupon["discount_percent"],
                           not coupon["active"])
        flash(t("coupon_saved"), "ok")
    return redirect(url_for("admin_coupons"))


# @app.route("/admin/coupons/<int:cid>/delete", methods=["POST"])
@admin_required
@permission_required("coupons")
def admin_coupon_delete(cid):
    repo.delete_coupon(cid)
    flash(t("coupon_deleted"), "ok")
    return redirect(url_for("admin_coupons"))


# --- Администраторы (только генеральный) ---

def superadmin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        admin = session.get("admin")
        if not admin:
            return redirect(url_for("login"))
        if admin.get("role") != "superadmin":
            flash(t("no_permission"), "error")
            return redirect(url_for("admin_dashboard"))
        return view(*args, **kwargs)
    return wrapped


def parse_permissions(form):
    """Собирает список прав из чекбоксов формы."""
    keys = []
    for key in PERMISSION_KEYS:
        if form.get(key):
            keys.append(key)
    return keys


# @app.route("/admin/admins")
@admin_required
@superadmin_required
def admin_admins():
    admins = repo.get_admins()
    return render_template("admin/admins.html", admins=admins,
                           permissions=PERMISSIONS)


# @app.route("/admin/admins/new", methods=["GET", "POST"])
@admin_required
@superadmin_required
def admin_admin_new():
    form = AdminForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        if repo.get_admin_by_username(username):
            flash(t("admin_exists"), "error")
            return render_template("admin/admin_form.html", form=form,
                                   permissions=PERMISSIONS, edit=False)
        perms = parse_permissions(request.form)
        repo.create_admin(
            username=username,
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
            permissions=perms,
        )
        flash(t("admin_saved"), "ok")
        return redirect(url_for("admin_admins"))
    return render_template("admin/admin_form.html", form=form,
                           permissions=PERMISSIONS, edit=False)


# @app.route("/admin/admins/<int:aid>/edit", methods=["GET", "POST"])
@admin_required
@superadmin_required
def admin_admin_edit(aid):
    target = repo.get_admin_by_id(aid)
    if not target:
        abort(404)
    form = AdminEditForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        existing = repo.get_admin_by_username(username)
        if existing and existing["id"] != aid:
            flash(t("admin_exists"), "error")
            return render_template("admin/admin_form.html", form=form,
                                   permissions=PERMISSIONS, edit=True, admin=target)
        perms = parse_permissions(request.form)
        kwargs = {"username": username, "role": form.role.data, "permissions": perms}
        if form.password.data:
            kwargs["password_hash"] = generate_password_hash(form.password.data)
        repo.update_admin(aid, username, **kwargs)
        flash(t("admin_saved"), "ok")
        return redirect(url_for("admin_admins"))
    if not form.is_submitted():
        form.username.data = target["username"]
        form.role.data = target["role"]
        perms = target.get("permissions") or []
        if isinstance(perms, str):
            import json as _json
            try:
                perms = _json.loads(perms)
            except Exception:
                perms = []
        form.permissions.data = ",".join(perms)
    return render_template("admin/admin_form.html", form=form,
                           permissions=PERMISSIONS, edit=True, admin=target)


# @app.route("/admin/admins/<int:aid>/delete", methods=["POST"])
@admin_required
@superadmin_required
def admin_admin_delete(aid):
    current = session.get("admin", {})
    if current.get("id") == aid:
        flash(t("admin_cannot_delete_self"), "error")
        return redirect(url_for("admin_admins"))
    repo.delete_admin(aid)
    flash(t("admin_deleted"), "ok")
    return redirect(url_for("admin_admins"))


# --- Категории ---

# @app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
@permission_required("categories")
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


# @app.route("/admin/categories/<int:cid>/delete", methods=["POST"])
@admin_required
@permission_required("categories")
def admin_category_delete(cid):
    repo.delete_category(cid)
    flash(t("category_deleted"), "ok")
    return redirect(url_for("admin_categories"))


# --- Города (доставка) ---

# @app.route("/admin/cities", methods=["GET", "POST"])
@admin_required
@permission_required("cities")
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


# @app.route("/admin/cities/<int:cid>/delete", methods=["POST"])
@admin_required
@permission_required("cities")
def admin_city_delete(cid):
    repo.delete_city(cid)
    flash(t("city_deleted"), "ok")
    return redirect(url_for("admin_cities"))


# ---------- JSON API (для React-фронтенда) ----------

def serialize_row(row):
    """Преобразует строку БД в JSON-совместимый dict."""
    if row is None:
        return None
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, (datetime, date)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def api_admin():
    """Текущий админ для API (из сессии)."""
    admin = session.get("admin")
    return admin if admin else None


def api_admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        admin = api_admin()
        if not admin:
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        return view(admin, *args, **kwargs)
    return wrapped


@app.route("/api/img/<path:name>")
def api_img(name):
    """Отдаёт картинку из static/img через API (работает через Vite-прокси)."""
    safe = os.path.basename(name)
    path = os.path.join(app.root_path, "static", "img", safe)
    if not os.path.exists(path):
        abort(404)
    from flask import send_from_directory
    return send_from_directory(os.path.join(app.root_path, "static", "img"), safe)


@app.route("/api/lang/<lang>", methods=["POST"])
def api_set_lang(lang):
    if lang in ("ru", "uz"):
        session["lang"] = lang
    return jsonify({"ok": True, "lang": get_lang()})


@app.route("/api/categories")
def api_categories():
    cats = repo.get_categories()
    return jsonify({"ok": True, "categories": [serialize_row(c) for c in cats]})


@app.route("/api/cities")
def api_cities():
    cities = repo.get_cities()
    return jsonify({"ok": True, "cities": [serialize_row(c) for c in cities]})


@app.route("/api/products")
def api_products():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    sort = request.args.get("sort", "popular")
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()
    page = request.args.get("page", 1, type=int)
    filters = {"q": q, "category": category, "sort": sort, "page": page, "per_page": 12}
    if min_price:
        filters["min_price"] = min_price
    if max_price:
        filters["max_price"] = max_price
    if request.args.get("in_stock") == "1":
        filters["in_stock"] = "1"
    if request.args.get("on_sale") == "1":
        filters["on_sale"] = "1"
    products, total, page, per_page = repo.get_products(filters)
    total_pages = max(1, (total + per_page - 1) // per_page)
    return jsonify({
        "ok": True,
        "products": [serialize_row(p) for p in products],
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "per_page": per_page,
    })


@app.route("/api/products/<int:pid>")
def api_product(pid):
    p = repo.get_product(pid)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404
    related = repo.get_related(pid, p["category_id"])
    images = repo.get_product_images(pid)
    specs = repo.parse_specs(p.get("specs"))
    reviews = repo.get_reviews(pid, approved_only=True)
    return jsonify({
        "ok": True,
        "product": serialize_row(p),
        "related": [serialize_row(r) for r in related],
        "images": [serialize_row(i) for i in images],
        "specs": specs,
        "reviews": [{
            "id": r["id"], "customer_name": r["customer_name"],
            "rating": r["rating"], "text": r["text"],
            "created_at": r["created_at"].strftime("%d.%m.%Y") if r["created_at"] else "",
        } for r in reviews],
    })


@app.route("/api/products/<int:pid>/review", methods=["POST"])
def api_product_review(pid):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    text = (data.get("text") or "").strip()
    rating = data.get("rating")
    if not name or not text or not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"ok": False, "error": "invalid"}), 400
    p = repo.get_product(pid)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404
    repo.create_review(pid, name, rating, text)
    return jsonify({"ok": True})


@app.route("/api/cart")
def api_cart():
    items, total = cart_items_data()
    return jsonify({
        "ok": True,
        "items": items,
        "total": total,
        "count": sum(_get_cart_store().values()),
    })


@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    data = request.get_json(silent=True) or request.form
    pid = str(data.get("product_id", ""))
    if not pid.isdigit():
        return jsonify({"ok": False, "error": "invalid"}), 400
    qty = int(data.get("qty", 1) or 1)
    qty = max(1, min(qty, 99))
    cart = _get_cart_store()
    cart[pid] = cart.get(pid, 0) + qty
    _save_cart_store(cart)
    return jsonify({"ok": True, "cart_count": sum(cart.values()), "qty": cart[pid]})


@app.route("/api/cart/update", methods=["POST"])
def api_cart_update():
    data = request.get_json(silent=True) or request.form
    pid = str(data.get("product_id", ""))
    qty = int(data.get("qty", 1) or 1)
    cart = _get_cart_store()
    if qty <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = min(qty, 99)
    _save_cart_store(cart)
    items, total = cart_items_data()
    return jsonify({"ok": True, "count": sum(cart.values()),
                    "items": items, "total": total})


@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    data = request.get_json(silent=True) or request.form
    pid = str(data.get("product_id", ""))
    cart = _get_cart_store()
    cart.pop(pid, None)
    _save_cart_store(cart)
    items, total = cart_items_data()
    return jsonify({"ok": True, "count": sum(cart.values()),
                    "items": items, "total": total})


@app.route("/api/wishlist")
def api_wishlist():
    wish = _get_wish_store()
    products = []
    if wish:
        ids = [int(i) for i in wish]
        products = repo.get_products_by_ids(ids)
    return jsonify({"ok": True, "products": [serialize_row(p) for p in products]})


@app.route("/api/wishlist/toggle", methods=["POST"])
def api_wishlist_toggle():
    data = request.get_json(silent=True) or request.form
    pid = str(data.get("product_id", ""))
    if not pid.isdigit():
        return jsonify({"ok": False, "error": "invalid"}), 400
    wish = _get_wish_store()
    if pid in wish:
        wish.discard(pid)
        added = False
    else:
        wish.add(pid)
        added = True
    _save_wish_store(wish)
    return jsonify({"ok": True, "added": added, "wish_count": len(wish)})


@app.route("/api/compare")
def api_compare():
    compare = _get_compare_store()
    products = []
    if compare:
        ids = [int(i) for i in compare]
        products = repo.get_products_by_ids(ids)
    return jsonify({"ok": True, "products": [serialize_row(p) for p in products]})


@app.route("/api/compare/toggle", methods=["POST"])
def api_compare_toggle():
    data = request.get_json(silent=True) or request.form
    pid = str(data.get("product_id", ""))
    if not pid.isdigit():
        return jsonify({"ok": False, "error": "invalid"}), 400
    compare = _get_compare_store()
    if len(compare) >= 4 and pid not in compare:
        return jsonify({"ok": False, "error": "compare_limit"}), 400
    if pid in compare:
        compare.discard(pid)
        added = False
    else:
        compare.add(pid)
        added = True
    _save_compare_store(compare)
    return jsonify({"ok": True, "added": added, "compare_count": len(compare)})


@app.route("/api/compare/remove", methods=["POST"])
def api_compare_remove():
    data = request.get_json(silent=True) or request.form
    pid = str(data.get("product_id", ""))
    compare = _get_compare_store()
    compare.discard(pid)
    _save_compare_store(compare)
    return jsonify({"ok": True, "compare_count": len(compare)})


@app.route("/api/checkout/coupon", methods=["POST"])
def api_coupon_check():
    data = request.get_json(silent=True) or request.form
    code = (data.get("code") or "").strip().upper()
    items, total = cart_items_data()
    if not items:
        return jsonify({"ok": False, "error": "cart_empty"})
    coupon = repo.get_coupon(code) if code else None
    if coupon:
        discount = round(total * coupon["discount_percent"] / 100, 2)
        return jsonify({"ok": True, "code": coupon["code"],
                        "percent": coupon["discount_percent"], "discount": discount})
    return jsonify({"ok": False, "error": "invalid"})


@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False, "error": "auth_required"}), 401
    lang = get_lang()
    items, total = cart_items_data()
    if not items:
        return jsonify({"ok": False, "error": "cart_empty"}), 400
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip() or None
    city_id = data.get("city_id")
    address = (data.get("address") or "").strip()
    address2 = (data.get("address2") or "").strip() or None
    coupon_code = (data.get("coupon") or "").strip().upper()
    if not name or len(name) < 2 or not phone or not address or len(address) < 5:
        return jsonify({"ok": False, "error": "invalid_fields"}), 400
    city = repo.get_city(int(city_id)) if city_id else None
    if not city:
        return jsonify({"ok": False, "error": "invalid_city"}), 400

    discount = 0
    coupon = repo.get_coupon(coupon_code) if coupon_code else None
    if coupon:
        discount = round(total * coupon["discount_percent"] / 100, 2)

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
        customer_name=name, phone=phone, email=email,
        city=city_name, address=address, address2=address2,
        delivery_price=delivery_price, delivery_minutes=delivery_minutes,
        subtotal=subtotal, discount=discount,
        coupon_code=coupon_code if coupon else None,
        total=grand_total, items=order_items,
    )
    uid = session.get("user_id")
    if uid:
        repo.update_order_user(order_id, uid)
    order = repo.get_order(order_id)
    if order:
        send_telegram_notification(order)
        send_order_email(order)
    session["cart"] = {}
    return jsonify({
        "ok": True,
        "order_id": order_id, "total": grand_total,
        "delivery_price": delivery_price, "delivery_minutes": delivery_minutes,
        "discount": discount, "coupon_code": coupon_code if coupon else "",
    })


@app.route("/api/track/<int:oid>")
def api_track(oid):
    order = repo.get_order(oid)
    if not order:
        return jsonify({"ok": False, "error": "not_found"}), 404
    items = repo.get_order_items(oid)
    return jsonify({
        "ok": True,
        "order": serialize_row(order),
        "items": [serialize_row(i) for i in items],
    })


# ---------- Пользователи (клиенты) ----------

@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip() or None
    if not username or len(username) < 3 or len(password) < 4 or not email:
        return jsonify({"ok": False, "error": "invalid_fields"}), 400
    if "@" not in email or "." not in email:
        return jsonify({"ok": False, "error": "invalid_email"}), 400
    if repo.get_user_by_username(username):
        return jsonify({"ok": False, "error": "exists"}), 400
    repo.create_user(username, generate_password_hash(password), email)
    user = repo.get_user_by_username(username)
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    _merge_guest_data(user["id"])
    return jsonify({"ok": True, "user": {"id": user["id"], "username": user["username"]}})


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = repo.get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        _merge_guest_data(user["id"])
        return jsonify({"ok": True, "user": {"id": user["id"], "username": user["username"]}})
    return jsonify({"ok": False, "error": "invalid_credentials"}), 401


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return jsonify({"ok": True})


@app.route("/api/auth/me")
def api_me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False}), 401
    user = repo.get_user_by_id(uid)
    if not user:
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "user": {"id": user["id"], "username": user["username"]}})


@app.route("/api/my-orders")
def api_my_orders():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    orders = repo.get_user_orders(uid)
    result = []
    for o in orders:
        items = repo.get_order_items(o["id"])
        result.append({"order": serialize_row(o),
                       "items": [serialize_row(i) for i in items]})
    return jsonify({"ok": True, "orders": result})


# ---------- Админ API ----------

@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    admin = repo.get_admin_by_username(username)
    if admin and check_password_hash(admin["password_hash"], password):
        perms = admin.get("permissions") or []
        if isinstance(perms, str):
            try:
                perms = json.loads(perms)
            except Exception:
                perms = []
        session["admin"] = {
            "id": admin["id"], "username": admin["username"],
            "role": admin["role"], "permissions": perms,
        }
        return jsonify({"ok": True, "admin": {
            "id": admin["id"], "username": admin["username"],
            "role": admin["role"], "permissions": perms,
        }})
    return jsonify({"ok": False, "error": "invalid_credentials"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def api_admin_logout():
    session.pop("admin", None)
    session.pop("admin_id", None)
    return jsonify({"ok": True})


@app.route("/api/admin/me")
def api_admin_me():
    admin = api_admin()
    if not admin:
        return jsonify({"ok": False}), 401
    fresh = repo.get_admin_by_id(admin["id"])
    return jsonify({"ok": True, "admin": {
        "id": fresh["id"], "username": fresh["username"],
        "role": fresh["role"],
        "permissions": fresh.get("permissions") or [],
    }})


@app.route("/api/admin/orders")
@api_admin_required
def api_admin_orders(admin):
    status_filter = request.args.get("status", "")
    orders = repo.get_orders(status_filter or None)
    result = []
    for o in orders:
        order_items = repo.get_order_items(o["id"])
        result.append({"order": serialize_row(o),
                       "order_items": [serialize_row(i) for i in order_items]})
    return jsonify({"ok": True, "orders": result})


@app.route("/api/admin/orders/<int:oid>/status", methods=["POST"])
@api_admin_required
def api_admin_order_status(admin, oid):
    if not repo.admin_has_permission(admin, "orders"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    data = request.get_json(silent=True) or {}
    status = data.get("status", "")
    if status not in STATUSES:
        return jsonify({"ok": False, "error": "invalid_status"}), 400
    repo.update_order_status(oid, status)
    return jsonify({"ok": True})


@app.route("/api/admin/products")
@api_admin_required
def api_admin_products(admin):
    products, _, _, _ = repo.get_products({"sort": "popular", "per_page": 999})
    return jsonify({"ok": True, "products": [serialize_row(p) for p in products]})


@app.route("/api/admin/products", methods=["POST"])
@api_admin_required
def api_admin_product_create(admin):
    if not repo.admin_has_permission(admin, "products"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    data = request.get_json(silent=True) or {}
    required = ["category_id", "name_ru", "name_uz", "description_ru", "description_uz", "price", "stock"]
    if any(not data.get(k) for k in required):
        return jsonify({"ok": False, "error": "invalid_fields"}), 400
    specs_json = json.dumps(data.get("specs", []), ensure_ascii=False)
    result = repo.create_product({
        "category_id": int(data["category_id"]),
        "name_ru": data["name_ru"], "name_uz": data["name_uz"],
        "description_ru": data["description_ru"], "description_uz": data["description_uz"],
        "price": data["price"], "old_price": data.get("old_price"),
        "stock": data["stock"], "image": data.get("image") or "no-image.png",
        "rating": data.get("rating", 5.0), "reviews": data.get("reviews", 0),
        "specs_json": specs_json,
    })
    return jsonify({"ok": True, "id": result["id"] if result else None})


@app.route("/api/admin/products/<int:pid>", methods=["PUT"])
@api_admin_required
def api_admin_product_update(admin, pid):
    if not repo.admin_has_permission(admin, "products"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    p = repo.get_product(pid)
    if not p:
        return jsonify({"ok": False, "error": "not_found"}), 404
    data = request.get_json(silent=True) or {}
    specs_json = json.dumps(data.get("specs", []), ensure_ascii=False)
    repo.update_product(pid, {
        "category_id": int(data.get("category_id", p["category_id"])),
        "name_ru": data.get("name_ru", p["name_ru"]),
        "name_uz": data.get("name_uz", p["name_uz"]),
        "description_ru": data.get("description_ru", p["description_ru"]),
        "description_uz": data.get("description_uz", p["description_uz"]),
        "price": data.get("price", p["price"]),
        "old_price": data.get("old_price", p["old_price"]),
        "stock": data.get("stock", p["stock"]),
        "image": data.get("image", p["image"]),
        "rating": data.get("rating", p["rating"]),
        "reviews": data.get("reviews", p["reviews"]),
        "specs_json": specs_json,
    })
    return jsonify({"ok": True})


@app.route("/api/admin/products/<int:pid>", methods=["DELETE"])
@api_admin_required
def api_admin_product_delete(admin, pid):
    if not repo.admin_has_permission(admin, "products"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    repo.delete_product(pid)
    return jsonify({"ok": True})


@app.route("/api/admin/dashboard")
@api_admin_required
def api_admin_dashboard(admin):
    if not repo.admin_has_permission(admin, "dashboard"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    summary = repo.analytics_summary()
    by_status = repo.analytics_orders_by_status()
    sales = repo.analytics_sales_by_day(14)
    sales_months = repo.analytics_sales_by_month(6)
    top = repo.analytics_top_products(5)
    recent = repo.analytics_recent_orders(8)
    status_map = {row["status"]: row["count"] for row in by_status}
    return jsonify({
        "ok": True,
        "summary": {k: (float(v) if isinstance(v, Decimal) else v) for k, v in summary.items()},
        "status_map": status_map,
        "sales": [serialize_row(s) for s in sales],
        "sales_months": [serialize_row(m) for m in sales_months],
        "top": [serialize_row(tp) for tp in top],
        "recent": [serialize_row(o) for o in recent],
    })


@app.route("/api/admin/reviews")
@api_admin_required
def api_admin_reviews(admin):
    if not repo.admin_has_permission(admin, "reviews"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    reviews = repo.get_all_reviews()
    return jsonify({"ok": True, "reviews": [{
        "id": r["id"], "product_id": r["product_id"],
        "product_name": r.get("product_ru"), "customer_name": r["customer_name"],
        "rating": r["rating"], "text": r["text"], "approved": r["approved"],
        "created_at": r["created_at"].strftime("%d.%m.%Y") if r["created_at"] else "",
    } for r in reviews]})


@app.route("/api/admin/reviews/<int:rid>", methods=["DELETE"])
@api_admin_required
def api_admin_review_delete(admin, rid):
    if not repo.admin_has_permission(admin, "reviews"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    review = db.fetch_one("SELECT * FROM reviews WHERE id=%s", (rid,))
    if review:
        repo.delete_review(rid)
        repo.recalc_product_rating(review["product_id"])
    return jsonify({"ok": True})


@app.route("/api/admin/coupons")
@api_admin_required
def api_admin_coupons(admin):
    if not repo.admin_has_permission(admin, "coupons"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    coupons = repo.get_coupons()
    return jsonify({"ok": True, "coupons": [serialize_row(c) for c in coupons]})


@app.route("/api/admin/coupons", methods=["POST"])
@api_admin_required
def api_admin_coupon_create(admin):
    if not repo.admin_has_permission(admin, "coupons"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    percent = data.get("discount_percent")
    if not code or not percent:
        return jsonify({"ok": False, "error": "invalid_fields"}), 400
    repo.create_coupon(code, int(percent))
    return jsonify({"ok": True})


@app.route("/api/admin/coupons/<int:cid>/toggle", methods=["POST"])
@api_admin_required
def api_admin_coupon_toggle(admin, cid):
    if not repo.admin_has_permission(admin, "coupons"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    coupon = db.fetch_one("SELECT * FROM coupons WHERE id=%s", (cid,))
    if coupon:
        repo.update_coupon(cid, coupon["code"], coupon["discount_percent"], not coupon["active"])
    return jsonify({"ok": True})


@app.route("/api/admin/coupons/<int:cid>", methods=["DELETE"])
@api_admin_required
def api_admin_coupon_delete(admin, cid):
    if not repo.admin_has_permission(admin, "coupons"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    repo.delete_coupon(cid)
    return jsonify({"ok": True})


@app.route("/api/admin/categories", methods=["GET"])
@api_admin_required
def api_admin_categories(admin):
    cats = repo.get_categories()
    return jsonify({"ok": True, "categories": [serialize_row(c) for c in cats]})


@app.route("/api/admin/categories", methods=["POST"])
@api_admin_required
def api_admin_category_create(admin):
    if not repo.admin_has_permission(admin, "categories"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    data = request.get_json(silent=True) or {}
    slug, name_ru, name_uz, icon = (data.get("slug") or "").strip(), \
        (data.get("name_ru") or "").strip(), (data.get("name_uz") or "").strip(), \
        (data.get("icon") or "").strip()
    if not slug or not name_ru or not name_uz:
        return jsonify({"ok": False, "error": "invalid_fields"}), 400
    repo.create_category(slug, name_ru, name_uz, icon or "tag")
    return jsonify({"ok": True})


@app.route("/api/admin/categories/<int:cid>", methods=["DELETE"])
@api_admin_required
def api_admin_category_delete(admin, cid):
    if not repo.admin_has_permission(admin, "categories"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    repo.delete_category(cid)
    return jsonify({"ok": True})


@app.route("/api/admin/cities", methods=["GET"])
@api_admin_required
def api_admin_cities(admin):
    cities = repo.get_cities()
    return jsonify({"ok": True, "cities": [serialize_row(c) for c in cities]})


@app.route("/api/admin/cities", methods=["POST"])
@api_admin_required
def api_admin_city_create(admin):
    if not repo.admin_has_permission(admin, "cities"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    data = request.get_json(silent=True) or {}
    name_ru, name_uz = (data.get("name_ru") or "").strip(), (data.get("name_uz") or "").strip()
    price, mins = data.get("delivery_price"), data.get("delivery_minutes")
    if not name_ru or not name_uz or not price or not mins:
        return jsonify({"ok": False, "error": "invalid_fields"}), 400
    repo.create_city(name_ru, name_uz, float(price), int(mins))
    return jsonify({"ok": True})


@app.route("/api/admin/cities/<int:cid>", methods=["DELETE"])
@api_admin_required
def api_admin_city_delete(admin, cid):
    if not repo.admin_has_permission(admin, "cities"):
        return jsonify({"ok": False, "error": "no_permission"}), 403
    repo.delete_city(cid)
    return jsonify({"ok": True})


@app.route("/api/admin/admins")
@api_admin_required
def api_admin_admins(admin):
    if admin.get("role") != "superadmin":
        return jsonify({"ok": False, "error": "no_permission"}), 403
    admins = repo.get_admins()
    return jsonify({"ok": True, "admins": [{
        "id": a["id"], "username": a["username"], "role": a["role"],
        "permissions": a.get("permissions") or [],
    } for a in admins]})


@app.route("/api/admin/admins", methods=["POST"])
@api_admin_required
def api_admin_admin_create(admin):
    if admin.get("role") != "superadmin":
        return jsonify({"ok": False, "error": "no_permission"}), 403
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role", "manager")
    if not username or len(password) < 4:
        return jsonify({"ok": False, "error": "invalid_fields"}), 400
    if repo.get_admin_by_username(username):
        return jsonify({"ok": False, "error": "exists"}), 400
    repo.create_admin(username=username,
                      password_hash=generate_password_hash(password),
                      role=role if role in ("manager", "superadmin") else "manager",
                      permissions=data.get("permissions") or [])
    return jsonify({"ok": True})


@app.route("/api/admin/admins/<int:aid>", methods=["DELETE"])
@api_admin_required
def api_admin_admin_delete(admin, aid):
    if admin.get("role") != "superadmin":
        return jsonify({"ok": False, "error": "no_permission"}), 403
    if admin.get("id") == aid:
        return jsonify({"ok": False, "error": "cannot_delete_self"}), 400
    repo.delete_admin(aid)
    return jsonify({"ok": True})


# Отключаем CSRF для всех API-маршрутов (React шлёт JSON без токена)
for _rule in app.url_map.iter_rules():
    if _rule.rule.startswith("/api/"):
        _endpoint = _rule.endpoint
        _func = app.view_functions.get(_endpoint)
        if _func:
            csrf.exempt(_func)


# ---------- React SPA (отдача собранного фронтенда) ----------

def _react_dir():
    return os.path.join(app.root_path, "react-dist")


@app.route("/assets/<path:filename>")
def react_assets(filename):
    from flask import send_from_directory
    safe = os.path.basename(filename)
    path = os.path.join(_react_dir(), "assets", safe)
    if not os.path.exists(path):
        abort(404)
    return send_from_directory(os.path.join(_react_dir(), "assets"), safe)


@app.route("/favicon.svg")
def react_favicon():
    from flask import send_from_directory
    return send_from_directory(_react_dir(), "favicon.svg")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def react_spa(path):
    """Отдаёт index.html React для всех путей, кроме /api и /static (SPA-роутинг)."""
    from flask import send_from_directory
    if path.startswith("api/") or path.startswith("static/"):
        abort(404)
    # Проверяем, есть ли реальный файл в react-dist
    full = os.path.join(_react_dir(), path)
    if path and os.path.isfile(full):
        return send_from_directory(_react_dir(), path)
    return send_from_directory(_react_dir(), "index.html")


# ---------- Ошибки ----------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
