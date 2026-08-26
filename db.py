# -*- coding: utf-8 -*-
"""Создание БД tech_store, таблиц и наполнение демо-данными.
Запуск: python db.py
"""
import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash
import config

PRODUCTS = [
    # (category_slug, name_ru, name_uz, price, old_price, stock, image, rating, reviews)
    ("phones", "iPhone 15 Pro 256GB", "iPhone 15 Pro 256GB", 1150, 1250, 12, "iphone15pro.png", 4.9, 230),
    ("phones", "Samsung Galaxy S24 Ultra", "Samsung Galaxy S24 Ultra", 1050, 1120, 15, "s24ultra.png", 4.8, 180),
    ("phones", "Xiaomi Redmi Note 13 Pro", "Xiaomi Redmi Note 13 Pro", 320, 360, 40, "redminote13.png", 4.6, 410),
    ("phones", "Google Pixel 8", "Google Pixel 8", 700, None, 9, "pixel8.png", 4.7, 95),
    ("laptops", "MacBook Air M2 13\"", "MacBook Air M2 13\"", 1200, 1320, 8, "macbookair.png", 4.9, 150),
    ("laptops", "ASUS ROG Strix G16", "ASUS ROG Strix G16", 1500, 1650, 6, "rog.png", 4.8, 88),
    ("laptops", "Lenovo IdeaPad Slim 5", "Lenovo IdeaPad Slim 5", 620, None, 20, "ideapad.png", 4.5, 134),
    ("laptops", "HP Pavilion 15", "HP Pavilion 15", 540, 590, 14, "hp15.png", 4.4, 76),
    ("tablets", "iPad Air 11\"", "iPad Air 11\"", 650, 700, 10, "ipadair.png", 4.8, 64),
    ("tablets", "Samsung Galaxy Tab S9", "Samsung Galaxy Tab S9", 720, None, 7, "tabs9.png", 4.7, 52),
    ("tablets", "Xiaomi Pad 6", "Xiaomi Pad 6", 380, 420, 18, "pad6.png", 4.6, 110),
    ("tv", "Samsung 55\" Crystal UHD", "Samsung 55\" Crystal UHD", 620, 700, 11, "samsung55.png", 4.7, 89),
    ("tv", "LG 65\" OLED evo", "LG 65\" OLED evo", 1450, 1600, 4, "lgo65.png", 4.9, 45),
    ("tv", "Xiaomi TV A Pro 50\"", "Xiaomi TV A Pro 50\"", 380, None, 16, "xiaomi50.png", 4.5, 73),
    ("accessories", "AirPods Pro 2", "AirPods Pro 2", 240, 270, 30, "airpods.png", 4.8, 320),
    ("accessories", "Anker PowerBank 20000mAh", "Anker PowerBank 20000mAh", 60, None, 60, "powerbank.png", 4.7, 200),
    ("accessories", "Logitech MX Master 3S", "Logitech MX Master 3S", 100, 115, 25, "mx3s.png", 4.8, 145),
    ("accessories", "Samsung Galaxy Watch 6", "Samsung Galaxy Watch 6", 280, 320, 22, "watch6.png", 4.6, 98),
]

CATEGORIES = [
    ("phones", "Смартфоны", "Smartfonlar", "📱"),
    ("laptops", "Ноутбуки", "Noutbuklar", "💻"),
    ("tablets", "Планшеты", "Planshetlar", "📲"),
    ("tv", "Телевизоры", "Televizorlar", "📺"),
    ("accessories", "Аксессуары", "Aksessuarlar", "🎧"),
]

CITIES = [
    ("Ташкент", "Toshkent", 20000, 30),
    ("Самарканд", "Samarqand", 40000, 60),
    ("Бухара", "Buxoro", 45000, 70),
    ("Фергана", "Farg'ona", 50000, 90),
    ("Андижан", "Andijon", 50000, 90),
    ("Наманган", "Namangan", 50000, 85),
    ("Навои", "Navoiy", 40000, 65),
]

DESC_RU = "Оригинальная техника с официальной гарантией. Быстрая доставка по Узбекистану, оплата при получении."
DESC_UZ = "Rasmiy kafolatli original texnika. O'zbekiston bo'ylab tez yetkazib berish, olganda to'lash."


def get_conn():
    return psycopg2.connect(**config.dsn())


def ensure_database():
    conn = psycopg2.connect(
        dbname="postgres",
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=config.DB_PORT,
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (config.DB_NAME,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{config.DB_NAME}"')
        print(f"БД '{config.DB_NAME}' создана")
    else:
        print(f"БД '{config.DB_NAME}' уже существует")
    cur.close()
    conn.close()


def seed():
    conn = get_conn()
    cur = conn.cursor()
    with open("schema.sql", "r", encoding="utf-8") as f:
        cur.execute(f.read())

    for slug, ru, uz, icon in CATEGORIES:
        cur.execute(
            "INSERT INTO categories (slug, name_ru, name_uz, icon) VALUES (%s,%s,%s,%s)",
            (slug, ru, uz, icon),
        )
    cat_ids = {}
    cur.execute("SELECT slug, id FROM categories")
    for slug, cid in cur.fetchall():
        cat_ids[slug] = cid

    for cat_slug, ru, uz, price, old, stock, img, rating, reviews in PRODUCTS:
        cur.execute(
            """INSERT INTO products
               (category_id, name_ru, name_uz, description_ru, description_uz,
                price, old_price, stock, image, rating, reviews)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (cat_ids[cat_slug], ru, uz, DESC_RU, DESC_UZ,
             price, old, stock, img, rating, reviews),
        )

    for ru, uz, price, mins in CITIES:
        cur.execute(
            "INSERT INTO cities (name_ru, name_uz, delivery_price, delivery_minutes) VALUES (%s,%s,%s,%s)",
            (ru, uz, price, mins),
        )

    # Администратор по умолчанию
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")
    cur.execute(
        "INSERT INTO admins (username, password_hash) VALUES (%s,%s)",
        (admin_user, generate_password_hash(admin_pass)),
    )
    print(f"Администратор: {admin_user} / {admin_pass}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"Добавлено: категорий={len(CATEGORIES)}, товаров={len(PRODUCTS)}, городов={len(CITIES)}")


if __name__ == "__main__":
    ensure_database()
    seed()
    print("Готово!")
