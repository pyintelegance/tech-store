# -*- coding: utf-8 -*-
"""Слой доступа к базе данных: подключения и пул."""
import psycopg2
import psycopg2.extras
import config


def get_conn():
    """Создаёт новое подключение (autocommit) к БД."""
    conn = psycopg2.connect(**config.dsn())
    conn.autocommit = True
    return conn


def fetch_all(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=None):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()
    finally:
        conn.close()


def execute(sql, params=None):
    """INSERT/UPDATE/DELETE без возврата. Возвращает rowcount."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.rowcount
    finally:
        conn.close()


def execute_returning(sql, params=None):
    """INSERT ... RETURNING id."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
            return row
    finally:
        conn.close()


def transaction(queries):
    """Выполняет список (sql, params) в одной транзакции (commit/rollback)."""
    conn = psycopg2.connect(**config.dsn())
    try:
        with conn.cursor() as cur:
            for sql, params in queries:
                cur.execute(sql, params or ())
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()