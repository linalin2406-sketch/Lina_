# -*- coding: utf-8 -*-
"""
Список RSS-лент, из которых портал собирает новости.

Формат одной строки:  ("Название", "адрес RSS", filter_books)
  - region "ru"  -> вкладка «Россия», "int" -> вкладка «За рубежом»
  - filter_books = False -> берём ВСЕ новости из ленты (лента уже про книги)
  - filter_books = True  -> берём ТОЛЬКО записи про книги (для общих новостных
                            лент вроде ТАСС, где книги — лишь малая часть).

Чтобы ДОБАВИТЬ источник — впишите строку по образцу.
Чтобы УБРАТЬ — удалите строку или поставьте # в её начале.
Если лента однажды перестанет работать — приложение просто её пропустит.
"""

# --- Российские источники ---
# Книжные ленты (берём целиком):
RU_FEEDS = [
    ("Год Литературы",        "https://godliteratury.ru/rss/",                  False),
    ("Лента.ру — Книги",      "https://lenta.ru/rss/news/culture/books",        False),
    ("Лента.ру — Книги (статьи)", "https://lenta.ru/rss/articles/culture/books", False),
    # Крупные новостные ленты — оставляем только новости про книги:
    ("ТАСС",                  "https://tass.ru/rss/v2.xml",                     True),
    ("Российская газета",     "https://rg.ru/xml/index.xml",                    True),
    ("Нож",                   "https://knife.media/feed/",                      True),
    ("Meduza",                "https://meduza.io/rss/all",                      True),
]

# --- Зарубежные источники (все специализированы на книгах) ---
INT_FEEDS = [
    ("The Guardian Books",    "https://www.theguardian.com/books/rss",          False),
    ("Literary Hub",          "https://lithub.com/feed/",                       False),
    ("Book Riot",             "https://bookriot.com/feed/",                     False),
    ("The Millions",          "https://themillions.com/feed",                   False),
    ("NYT Books",             "https://rss.nytimes.com/services/xml/rss/nyt/Books.xml", False),
    ("Publishers Weekly",     "https://www.publishersweekly.com/pw/feeds/recent/index.xml", False),
]

# Ключевые слова, по которым распознаём «книжную» новость в общих лентах.
BOOK_KEYWORDS = [
    "книг", "писател", "литератур", "роман", "издательств", "поэт", "поэзи",
    "бестселлер", "проза", "прозаик", "библиотек", "book", "novel",
    "нон-фикшн", "нонфикшн", "букер", "книжн",
]


def all_feeds():
    """Возвращает единый список кортежей (регион, название, url, filter_books)."""
    feeds = []
    for name, url, flt in RU_FEEDS:
        feeds.append(("ru", name, url, flt))
    for name, url, flt in INT_FEEDS:
        feeds.append(("int", name, url, flt))
    return feeds
