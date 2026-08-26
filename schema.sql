-- Схема базы данных магазина техники tech-store
-- Запуск: python db.py (создаёт БД, таблицы и наполняет данными)

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cities;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name_ru VARCHAR(100) NOT NULL,
    name_uz VARCHAR(100) NOT NULL,
    icon VARCHAR(10) NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    name_ru VARCHAR(200) NOT NULL,
    name_uz VARCHAR(200) NOT NULL,
    description_ru TEXT NOT NULL,
    description_uz TEXT NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    old_price NUMERIC(12,2),
    stock INTEGER NOT NULL DEFAULT 0,
    image VARCHAR(255) NOT NULL,
    rating NUMERIC(2,1) NOT NULL DEFAULT 5.0,
    reviews INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name_ru VARCHAR(100) NOT NULL,
    name_uz VARCHAR(100) NOT NULL,
    delivery_price NUMERIC(10,2) NOT NULL,
    delivery_minutes INTEGER NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(200) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(500) NOT NULL,
    address2 VARCHAR(500),
    delivery_price NUMERIC(10,2) NOT NULL,
    delivery_minutes INTEGER NOT NULL,
    total NUMERIC(12,2) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'new',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_name VARCHAR(200) NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    quantity INTEGER NOT NULL
);

CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
