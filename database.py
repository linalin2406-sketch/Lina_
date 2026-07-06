# -*- coding: utf-8 -*-
"""
Работа с локальной базой данных (SQLite).

База — это один файл books.db, который создаётся автоматически рядом
с приложением. Никакой отдельной установки СУБД не нужно.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "books.db"


def get_connection():
    """Открывает соединение с базой. Row -> доступ к колонкам по имени."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицу новостей, если её ещё нет."""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            link        TEXT    NOT NULL UNIQUE,   -- уникальная ссылка = защита от дублей
            summary     TEXT,
            published   TEXT,                      -- дата публикации (ISO-строка)
            source      TEXT,                      -- название источника
            region      TEXT,                      -- 'ru' или 'int'
            fetched_at  TEXT                        -- когда мы её скачали
        )
        """
    )
    conn.commit()
    conn.close()


def save_article(article):
    """
    Сохраняет одну новость. Если ссылка уже есть в базе — тихо пропускает
    (INSERT OR IGNORE). Возвращает True, если запись действительно добавлена.
    """
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO articles
            (title, link, summary, published, source, region, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            article["title"],
            article["link"],
            article["summary"],
            article["published"],
            article["source"],
            article["region"],
            article["fetched_at"],
        ),
    )
    conn.commit()
    added = cur.rowcount > 0
    conn.close()
    return added


def get_articles(region=None, source=None, query=None, limit=60):
    """Возвращает новости с учётом фильтров, самые свежие — первыми."""
    sql = "SELECT * FROM articles WHERE 1=1"
    params = []
    if region in ("ru", "int"):
        sql += " AND region = ?"
        params.append(region)
    if source:
        sql += " AND source = ?"
        params.append(source)
    if query:
        sql += " AND (title LIKE ? OR summary LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like])
    sql += " ORDER BY published DESC, id DESC LIMIT ?"
    params.append(limit)

    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sources(region=None):
    """Список источников (для выпадающего фильтра)."""
    sql = "SELECT DISTINCT source, region FROM articles"
    params = []
    if region in ("ru", "int"):
        sql += " WHERE region = ?"
        params.append(region)
    sql += " ORDER BY source"
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_articles():
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    conn.close()
    return n
