# -*- coding: utf-8 -*-
"""Создание БД tech_store, таблиц и наполнение демо-данными.
Запуск: python db.py
"""
import os
import json
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash
import config

PRODUCTS = [
    # (cat, name_ru, name_uz, price, old, stock, img, rating, reviews, specs [[k,v],...], extra_images [url,...])
    ("phones", "iPhone 15 Pro 256GB", "iPhone 15 Pro 256GB", 1150, 1250, 12, "iphone15pro.png", 4.9, 230,
     [["Экран", "6.1\" OLED 120Hz"], ["Камера", "48 Мп + 12 Мп + 12 Мп"], ["Память", "256 ГБ"], ["Батарея", "3274 мАч"], ["Чип", "A17 Pro"], ["ОС", "iOS 17"]],
     ["s24ultra.png", "pixel8.png"]),
    ("phones", "Samsung Galaxy S24 Ultra", "Samsung Galaxy S24 Ultra", 1050, 1120, 15, "s24ultra.png", 4.8, 180,
     [["Экран", "6.8\" AMOLED 120Hz"], ["Камера", "200 Мп"], ["Память", "256 ГБ"], ["Батарея", "5000 мАч"], ["Чип", "Snapdragon 8 Gen 3"], ["ОС", "Android 14"], ["Стилус", "S Pen в комплекте"]],
     ["iphone15pro.png", "redminote13.png"]),
    ("phones", "Xiaomi Redmi Note 13 Pro", "Xiaomi Redmi Note 13 Pro", 320, 360, 40, "redminote13.png", 4.6, 410,
     [["Экран", "6.67\" AMOLED 120Hz"], ["Камера", "200 Мп"], ["Память", "256 ГБ"], ["Батарея", "5100 мАч"], ["Чип", "Snapdragon 7s Gen 2"], ["ОС", "Android 13"]],
     ["s24ultra.png", "pixel8.png"]),
    ("phones", "Google Pixel 8", "Google Pixel 8", 700, None, 9, "pixel8.png", 4.7, 95,
     [["Экран", "6.2\" OLED 120Hz"], ["Камера", "50 Мп + 12 Мп"], ["Память", "128 ГБ"], ["Батарея", "4575 мАч"], ["Чип", "Google Tensor G3"], ["ОС", "Android 14"]],
     ["iphone15pro.png", "redminote13.png"]),
    ("laptops", "MacBook Air M2 13\"", "MacBook Air M2 13\"", 1200, 1320, 8, "macbookair.png", 4.9, 150,
     [["Экран", "13.6\" Liquid Retina"], ["Чип", "Apple M2"], ["Память", "8 ГБ / 256 ГБ"], ["Батарея", "до 18 часов"], ["Вес", "1.24 кг"], ["ОС", "macOS"]],
     ["rog.png", "ideapad.png"]),
    ("laptops", "ASUS ROG Strix G16", "ASUS ROG Strix G16", 1500, 1650, 6, "rog.png", 4.8, 88,
     [["Экран", "16\" 165Hz"], ["Чип", "Intel Core i9"], ["Видео", "RTX 4060"], ["Память", "16 ГБ / 512 ГБ"], ["Клавиатура", "RGB подсветка"], ["ОС", "Windows 11"]],
     ["macbookair.png", "hp15.png"]),
    ("laptops", "Lenovo IdeaPad Slim 5", "Lenovo IdeaPad Slim 5", 620, None, 20, "ideapad.png", 4.5, 134,
     [["Экран", "15.6\" FHD"], ["Чип", "Ryzen 5 7530U"], ["Память", "16 ГБ / 512 ГБ"], ["Батарея", "до 12 часов"], ["Вес", "1.5 кг"], ["ОС", "Windows 11"]],
     ["macbookair.png", "hp15.png"]),
    ("laptops", "HP Pavilion 15", "HP Pavilion 15", 540, 590, 14, "hp15.png", 4.4, 76,
     [["Экран", "15.6\" FHD"], ["Чип", "Core i5-1335U"], ["Память", "8 ГБ / 512 ГБ"], ["Батарея", "до 10 часов"], ["ОС", "Windows 11"]],
     ["ideapad.png", "macbookair.png"]),
    ("tablets", "iPad Air 11\"", "iPad Air 11\"", 650, 700, 10, "ipadair.png", 4.8, 64,
     [["Экран", "11\" Liquid Retina"], ["Чип", "Apple M2"], ["Память", "128 ГБ"], ["Камера", "12 Мп"], ["Вес", "462 г"], ["ОС", "iPadOS 17"]],
     ["tabs9.png", "pad6.png"]),
    ("tablets", "Samsung Galaxy Tab S9", "Samsung Galaxy Tab S9", 720, None, 7, "tabs9.png", 4.7, 52,
     [["Экран", "11\" AMOLED 120Hz"], ["Чип", "Snapdragon 8 Gen 2"], ["Память", "128 ГБ"], ["Батарея", "8400 мАч"], ["ОС", "Android 13"]],
     ["ipadair.png", "pad6.png"]),
    ("tablets", "Xiaomi Pad 6", "Xiaomi Pad 6", 380, 420, 18, "pad6.png", 4.6, 110,
     [["Экран", "11\" LCD 144Hz"], ["Чип", "Snapdragon 870"], ["Память", "128 ГБ"], ["Батарея", "8840 мАч"], ["ОС", "MIUI for Pad"]],
     ["tabs9.png", "ipadair.png"]),
    ("tv", "Samsung 55\" Crystal UHD", "Samsung 55\" Crystal UHD", 620, 700, 11, "samsung55.png", 4.7, 89,
     [["Диагональ", "55\""], ["Разрешение", "4K UHD"], ["Матрица", "LED Crystal"], ["Частота", "60 Гц"], ["Smart TV", "Tizen"], ["HDMI", "3 порта"]],
     ["lgo65.png", "xiaomi50.png"]),
    ("tv", "LG 65\" OLED evo", "LG 65\" OLED evo", 1450, 1600, 4, "lgo65.png", 4.9, 45,
     [["Диагональ", "65\""], ["Разрешение", "4K UHD"], ["Матрица", "OLED evo"], ["Частота", "120 Гц"], ["Smart TV", "webOS 23"], ["HDMI", "4 порта"], ["Долби", "Dolby Vision"]],
     ["samsung55.png", "xiaomi50.png"]),
    ("tv", "Xiaomi TV A Pro 50\"", "Xiaomi TV A Pro 50\"", 380, None, 16, "xiaomi50.png", 4.5, 73,
     [["Диагональ", "50\""], ["Разрешение", "4K UHD"], ["Матрица", "LED"], ["Smart TV", "Google TV"], ["HDMI", "3 порта"]],
     ["samsung55.png", "lgo65.png"]),
    ("accessories", "AirPods Pro 2", "AirPods Pro 2", 240, 270, 30, "airpods.png", 4.8, 320,
     [["Тип", "TWS наушники"], ["Шумоподавление", "Активное"], ["Батарея", "до 30 часов"], ["Защита", "IPX4"], ["Чип", "Apple H2"], ["Зарядка", "USB-C + MagSafe"]],
     ["watch6.png", "powerbank.png"]),
    ("accessories", "Anker PowerBank 20000mAh", "Anker PowerBank 20000mAh", 60, None, 60, "powerbank.png", 4.7, 200,
     [["Ёмкость", "20000 мАч"], ["Порты", "2×USB-A + USB-C"], ["Мощность", "22.5 Вт"], ["Вес", "345 г"], ["Технология", "PowerIQ"]],
     ["mx3s.png", "airpods.png"]),
    ("accessories", "Logitech MX Master 3S", "Logitech MX Master 3S", 100, 115, 25, "mx3s.png", 4.8, 145,
     [["Тип", "Беспроводная мышь"], ["Сенсор", "8000 DPI"], ["Батарея", "до 70 дней"], ["Колесо", "SmartShift"], ["Подключение", "Bluetooth + USB"]],
     ["powerbank.png", "airpods.png"]),
    ("accessories", "Samsung Galaxy Watch 6", "Samsung Galaxy Watch 6", 280, 320, 22, "watch6.png", 4.6, 98,
     [["Экран", "1.5\" AMOLED"], ["Корпус", "44 мм"], ["Батарея", "425 мАч"], ["Датчики", "HR, GPS, SpO2"], ["Защита", "5ATM + IP68"], ["ОС", "Wear OS 4"]],
     ["airpods.png", "powerbank.png"]),
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

COUPONS = [
    ("WELCOME10", 10),
    ("SALE15", 15),
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

    for item in PRODUCTS:
        cat_slug, ru, uz, price, old, stock, img, rating, reviews, specs, extra = item
        cur.execute(
            """INSERT INTO products
               (category_id, name_ru, name_uz, description_ru, description_uz,
                price, old_price, stock, image, rating, reviews, specs)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (cat_ids[cat_slug], ru, uz, DESC_RU, DESC_UZ,
             price, old, stock, img, rating, reviews,
             json.dumps(specs, ensure_ascii=False)),
        )
        pid = cur.fetchone()[0]
        for pos, extra_url in enumerate(extra):
            cur.execute(
                "INSERT INTO product_images (product_id, url, position) VALUES (%s,%s,%s)",
                (pid, extra_url, pos),
            )

    for ru, uz, price, mins in CITIES:
        cur.execute(
            "INSERT INTO cities (name_ru, name_uz, delivery_price, delivery_minutes) VALUES (%s,%s,%s,%s)",
            (ru, uz, price, mins),
        )

    for code, percent in COUPONS:
        cur.execute(
            "INSERT INTO coupons (code, discount_percent) VALUES (%s,%s)",
            (code, percent),
        )

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
    print(f"Добавлено: категорий={len(CATEGORIES)}, товаров={len(PRODUCTS)}, "
          f"городов={len(CITIES)}, купонов={len(COUPONS)}")


if __name__ == "__main__":
    ensure_database()
    seed()
    print("Готово!")