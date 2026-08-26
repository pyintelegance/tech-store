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
            price, old_price, stock, image, rating, reviews, specs)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
        (data["category_id"], data["name_ru"], data["name_uz"],
         data["description_ru"], data["description_uz"],
         data["price"], data.get("old_price"), data["stock"],
         data["image"], data.get("rating", 5.0), data.get("reviews", 0),
         data.get("specs_json", "[]")),
    )


def update_product(product_id, data):
    return db.execute(
        """UPDATE products SET category_id=%s, name_ru=%s, name_uz=%s,
           description_ru=%s, description_uz=%s, price=%s, old_price=%s,
           stock=%s, image=%s, rating=%s, reviews=%s, specs=%s WHERE id=%s""",
        (data["category_id"], data["name_ru"], data["name_uz"],
         data["description_ru"], data["description_uz"],
         data["price"], data.get("old_price"), data["stock"],
         data["image"], data.get("rating", 5.0), data.get("reviews", 0),
         data.get("specs_json", "[]"), product_id),
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


def create_order_full(customer_name, phone, city, address, address2,
                      delivery_price, delivery_minutes, subtotal, discount,
                      coupon_code, total, items):
    """Создаёт заказ с полными полями (скидки/промокод) в транзакции."""
    sql_order = (
        "INSERT INTO orders "
        "(customer_name, phone, city, address, address2, "
        "delivery_price, delivery_minutes, subtotal, discount, coupon_code, total, status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'new') RETURNING id"
    )
    conn = db.get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql_order, (
                customer_name, phone, city, address, address2,
                delivery_price, delivery_minutes, subtotal, discount,
                coupon_code, total,
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


# ---------- Характеристики (specs) ----------

def parse_specs(specs):
    """Принимает jsonb из БД или список пар, возвращает список [key, value]."""
    if specs is None:
        return []
    if isinstance(specs, list):
        return specs
    import json
    try:
        return json.loads(specs)
    except Exception:
        return []


# ---------- Галерея ----------

def get_product_images(product_id):
    return db.fetch_all(
        "SELECT * FROM product_images WHERE product_id=%s ORDER BY position, id",
        (product_id,),
    )


def add_product_image(product_id, url, position=0):
    return db.execute(
        "INSERT INTO product_images (product_id, url, position) VALUES (%s,%s,%s)",
        (product_id, url, position),
    )


def clear_product_images(product_id):
    return db.execute("DELETE FROM product_images WHERE product_id=%s", (product_id,))


# ---------- Отзывы ----------

def get_reviews(product_id, approved_only=True):
    if approved_only:
        return db.fetch_all(
            "SELECT * FROM reviews WHERE product_id=%s AND approved=TRUE "
            "ORDER BY created_at DESC",
            (product_id,),
        )
    return db.fetch_all(
        "SELECT * FROM reviews WHERE product_id=%s ORDER BY approved, created_at DESC",
        (product_id,),
    )


def get_all_reviews(status=None):
    if status == "pending":
        return db.fetch_all(
            "SELECT r.*, p.name_ru AS product_ru, p.name_uz AS product_uz "
            "FROM reviews r JOIN products p ON p.id=r.product_id "
            "WHERE r.approved=FALSE ORDER BY r.created_at DESC"
        )
    return db.fetch_all(
        "SELECT r.*, p.name_ru AS product_ru, p.name_uz AS product_uz "
        "FROM reviews r JOIN products p ON p.id=r.product_id "
        "ORDER BY r.created_at DESC"
    )


def create_review(product_id, customer_name, rating, text):
    """Создаёт отзыв сразу одобренным (без модерации)."""
    row = db.execute_returning(
        "INSERT INTO reviews (product_id, customer_name, rating, text, approved) "
        "VALUES (%s,%s,%s,%s,TRUE) RETURNING id",
        (product_id, customer_name, rating, text),
    )
    if row:
        recalc_product_rating(product_id)
    return row


def approve_review(review_id, approved=True):
    return db.execute(
        "UPDATE reviews SET approved=%s WHERE id=%s", (approved, review_id)
    )


def delete_review(review_id):
    return db.execute("DELETE FROM reviews WHERE id=%s", (review_id,))


def recalc_product_rating(product_id):
    """Пересчитывает рейтинг и число отзывов товара по одобренным."""
    row = db.fetch_one(
        "SELECT COALESCE(AVG(rating),5.0) AS avg_rating, COUNT(*) AS cnt "
        "FROM reviews WHERE product_id=%s AND approved=TRUE",
        (product_id,),
    )
    avg = float(row["avg_rating"]) if row else 5.0
    cnt = row["cnt"] if row else 0
    db.execute(
        "UPDATE products SET rating=%s, reviews=%s WHERE id=%s",
        (round(avg, 1), cnt, product_id),
    )
    return avg, cnt


# ---------- Промокоды ----------

def get_coupons():
    return db.fetch_all("SELECT * FROM coupons ORDER BY id")


def get_coupon(code):
    return db.fetch_one(
        "SELECT * FROM coupons WHERE UPPER(code)=UPPER(%s) AND active=TRUE",
        (code,),
    )


def create_coupon(code, discount_percent):
    return db.execute_returning(
        "INSERT INTO coupons (code, discount_percent) VALUES (%s,%s) RETURNING id",
        (code.upper(), discount_percent),
    )


def update_coupon(coupon_id, code, discount_percent, active):
    return db.execute(
        "UPDATE coupons SET code=%s, discount_percent=%s, active=%s WHERE id=%s",
        (code.upper(), discount_percent, active, coupon_id),
    )


def delete_coupon(coupon_id):
    return db.execute("DELETE FROM coupons WHERE id=%s", (coupon_id,))


# ---------- Администраторы ----------

def get_admins():
    return db.fetch_all(
        "SELECT id, username, role, permissions, created_at FROM admins ORDER BY id"
    )


def get_admin_by_id(admin_id):
    return db.fetch_one(
        "SELECT id, username, role, permissions, created_at FROM admins WHERE id=%s",
        (admin_id,),
    )


def get_admin_by_username(username):
    return db.fetch_one("SELECT * FROM admins WHERE username=%s", (username,))


def create_admin(username, password_hash, role="manager", permissions=None):
    import json as _json
    perms = _json.dumps(permissions or [], ensure_ascii=False)
    return db.execute_returning(
        "INSERT INTO admins (username, password_hash, role, permissions) "
        "VALUES (%s,%s,%s,%s) RETURNING id",
        (username, password_hash, role, perms),
    )


def update_admin(admin_id, username, password_hash=None, role=None, permissions=None):
    import json as _json
    if password_hash is not None or role is not None or permissions is not None:
        sets = []
        params = []
        if password_hash is not None:
            sets.append("password_hash=%s")
            params.append(password_hash)
        if role is not None:
            sets.append("role=%s")
            params.append(role)
        if permissions is not None:
            sets.append("permissions=%s")
            params.append(_json.dumps(permissions, ensure_ascii=False))
        params.append(admin_id)
        sets.append("username=%s") if False else None
        # username тоже обновляем если передали
        return db.execute(
            "UPDATE admins SET " + ", ".join(sets) + " WHERE id=%s", params
        )
    return 0


def delete_admin(admin_id):
    return db.execute("DELETE FROM admins WHERE id=%s", (admin_id,))


def admin_has_permission(admin, permission):
    """Проверяет право админа. Суперадмин имеет все права."""
    if admin.get("role") == "superadmin":
        return True
    perms = admin.get("permissions") or []
    import json as _json
    if isinstance(perms, str):
        try:
            perms = _json.loads(perms)
        except Exception:
            perms = []
    return permission in perms


# ---------- Аналитика ----------

def analytics_summary():
    """Сводные показатели для дашборда."""
    orders_total = db.fetch_one(
        "SELECT COUNT(*) AS count, COALESCE(SUM(total),0) AS sum FROM orders"
    )
    new_orders = db.fetch_one(
        "SELECT COUNT(*) AS count FROM orders WHERE status='new'"
    )
    products_total = db.fetch_one("SELECT COUNT(*) AS count FROM products")
    reviews_total = db.fetch_one(
        "SELECT COUNT(*) AS count FROM reviews WHERE approved=TRUE"
    )
    return {
        "orders_count": orders_total["count"],
        "revenue": float(orders_total["sum"]),
        "new_orders": new_orders["count"],
        "products_count": products_total["count"],
        "reviews_count": reviews_total["count"],
    }


def analytics_orders_by_status():
    return db.fetch_all(
        "SELECT status, COUNT(*) AS count FROM orders GROUP BY status"
    )


def analytics_sales_by_day(days=14):
    return db.fetch_all(
        """SELECT to_char(date_trunc('day', created_at), 'YYYY-MM-DD') AS day,
                  COUNT(*) AS count, SUM(total) AS total
           FROM orders
           WHERE created_at > now() - make_interval(days => %s)
           GROUP BY date_trunc('day', created_at)
           ORDER BY day ASC""",
        (int(days),),
    )


def analytics_top_products(limit=5):
    return db.fetch_all(
        """SELECT oi.product_name, SUM(oi.quantity) AS qty,
                  SUM(oi.price * oi.quantity) AS total
           FROM order_items oi
           GROUP BY oi.product_name
           ORDER BY qty DESC
           LIMIT %s""",
        (limit,),
    )


def analytics_recent_orders(limit=8):
    return db.fetch_all(
        "SELECT * FROM orders ORDER BY id DESC LIMIT %s", (limit,)
    )