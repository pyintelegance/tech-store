# -*- coding: utf-8 -*-
"""Repository — все SQL-запросы в одном месте (чистые функции)."""
import psycopg2.extras
import database as db

# ---------- Категории ----------

def get_categories():
    return db.fetch_all("SELECT * FROM categories ORDER BY id")


def get_category(category_id):
    return db.fetch_one("SELECT * FROM categories WHERE id=%s", (category_id,))


def create_category(slug, name_ru, name_uz, icon):
    return db.execute(
        "INSERT INTO categories (slug, name_ru, name_uz, icon) VALUES (%s,%s,%s,%s)",
        (slug, name_ru, name_uz, icon),
    )


def update_category(category_id, slug, name_ru, name_uz, icon):
    return db.execute(
        "UPDATE categories SET slug=%s, name_ru=%s, name_uz=%s, icon=%s WHERE id=%s",
        (slug, name_ru, name_uz, icon, category_id),
    )


def delete_category(category_id):
    return db.execute("DELETE FROM categories WHERE id=%s", (category_id,))


# ---------- Товары ----------

def get_products(filters=None):
    """filters: q, category, sort, min_price, max_price."""
    f = filters or {}
    where, params = [], []

    if f.get("q"):
        like = f"%{f['q']}%"
        where.append(
            "(p.name_ru ILIKE %s OR p.name_uz ILIKE %s OR "
            "p.description_ru ILIKE %s OR p.description_uz ILIKE %s)"
        )
        params += [like, like, like, like]
    if f.get("category"):
        where.append("p.category_id = %s")
        params.append(f["category"])
    if f.get("min_price"):
        where.append("p.price >= %s")
        params.append(f["min_price"])
    if f.get("max_price"):
        where.append("p.price <= %s")
        params.append(f["max_price"])

    order_map = {
        "popular": "ORDER BY p.reviews DESC, p.id ASC",
        "cheap": "ORDER BY p.price ASC",
        "expensive": "ORDER BY p.price DESC",
        "rating": "ORDER BY p.rating DESC, p.reviews DESC",
    }
    order = order_map.get(f.get("sort"), order_map["popular"])

    sql = (
        "SELECT p.*, c.slug AS cat_slug, c.icon AS cat_icon, "
        "c.name_ru AS cat_ru, c.name_uz AS cat_uz "
        "FROM products p JOIN categories c ON c.id = p.category_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " " + order
    return db.fetch_all(sql, params)


def get_product(product_id):
    return db.fetch_one(
        "SELECT p.*, c.slug AS cat_slug, c.icon AS cat_icon, "
        "c.name_ru AS cat_ru, c.name_uz AS cat_uz "
        "FROM products p JOIN categories c ON c.id = p.category_id "
        "WHERE p.id=%s",
        (product_id,),
    )


def get_related(product_id, category_id, limit=4):
    return db.fetch_all(
        "SELECT * FROM products WHERE category_id=%s AND id<>%s "
        "ORDER BY reviews DESC LIMIT %s",
        (category_id, product_id, limit),
    )


def get_products_by_ids(ids):
    if not ids:
        return []
    placeholders = ",".join(["%s"] * len(ids))
    return db.fetch_all(
        f"SELECT * FROM products WHERE id IN ({placeholders})", tuple(ids)
    )


def create_product(data):
    return db.execute_returning(
        """INSERT INTO products
           (category_id, name_ru, name_uz, description_ru, description_uz,
            price, old_price, stock, image, rating, reviews)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data["category_id"], data["name_ru"], data["name_uz"],
         data["description_ru"], data["description_uz"],
         data["price"], data.get("old_price"), data["stock"],
         data["image"], data.get("rating", 5.0), data.get("reviews", 0)),
    )


def update_product(product_id, data):
    return db.execute(
        """UPDATE products SET category_id=%s, name_ru=%s, name_uz=%s,
           description_ru=%s, description_uz=%s, price=%s, old_price=%s,
           stock=%s, image=%s, rating=%s, reviews=%s WHERE id=%s""",
        (data["category_id"], data["name_ru"], data["name_uz"],
         data["description_ru"], data["description_uz"],
         data["price"], data.get("old_price"), data["stock"],
         data["image"], data.get("rating", 5.0), data.get("reviews", 0),
         product_id),
    )


def delete_product(product_id):
    return db.execute("DELETE FROM products WHERE id=%s", (product_id,))


# ---------- Города (доставка) ----------

def get_cities():
    return db.fetch_all("SELECT * FROM cities ORDER BY id")


def get_city(city_id):
    return db.fetch_one("SELECT * FROM cities WHERE id=%s", (city_id,))


def create_city(name_ru, name_uz, delivery_price, delivery_minutes):
    return db.execute(
        "INSERT INTO cities (name_ru, name_uz, delivery_price, delivery_minutes) "
        "VALUES (%s,%s,%s,%s)",
        (name_ru, name_uz, delivery_price, delivery_minutes),
    )


def update_city(city_id, name_ru, name_uz, delivery_price, delivery_minutes):
    return db.execute(
        "UPDATE cities SET name_ru=%s, name_uz=%s, delivery_price=%s, "
        "delivery_minutes=%s WHERE id=%s",
        (name_ru, name_uz, delivery_price, delivery_minutes, city_id),
    )


def delete_city(city_id):
    return db.execute("DELETE FROM cities WHERE id=%s", (city_id,))


# ---------- Заказы ----------

def get_orders(status=None):
    if status:
        return db.fetch_all(
            "SELECT * FROM orders WHERE status=%s ORDER BY id DESC", (status,)
        )
    return db.fetch_all("SELECT * FROM orders ORDER BY id DESC")


def get_order(order_id):
    return db.fetch_one("SELECT * FROM orders WHERE id=%s", (order_id,))


def get_order_items(order_id):
    return db.fetch_all(
        "SELECT * FROM order_items WHERE order_id=%s", (order_id,)
    )


def update_order_status(order_id, status):
    return db.execute(
        "UPDATE orders SET status=%s WHERE id=%s", (status, order_id)
    )


def create_order(customer_name, phone, city, address, address2,
                 delivery_price, delivery_minutes, total, items):
    """Создаёт заказ + товары в одной транзакции. Возвращает order_id."""
    sql_order = (
        "INSERT INTO orders "
        "(customer_name, phone, city, address, address2, "
        "delivery_price, delivery_minutes, total, status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'new') RETURNING id"
    )
    conn = db.get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql_order, (
                customer_name, phone, city, address, address2,
                delivery_price, delivery_minutes, total,
            ))
            order_id = cur.fetchone()["id"]
            for it in items:
                cur.execute(
                    "INSERT INTO order_items (order_id, product_name, price, quantity) "
                    "VALUES (%s,%s,%s,%s)",
                    (order_id, it["name"], it["price"], it["qty"]),
                )
        conn.commit()
        return order_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()