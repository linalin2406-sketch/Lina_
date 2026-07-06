# -*- coding: utf-8 -*-
"""
Источники новостей и правила распределения по темам.

Портал показывает две темы:
  • "kids"      — тренды в детской литературе
  • "marketing" — тренды в маркетинге книг (ниша «книги»)

Формат одной строки:  ("регион", "Название", "адрес RSS", тема_по_умолчанию)
  - регион: "ru" или "int" — показывается маленькой пометкой на карточке
  - тема_по_умолчанию:
      "kids"      — вся лента считается детской литературой
      "marketing" — вся лента считается маркетингом книг
      None        — тема определяется по ключевым словам в заголовке/описании;
                    если тема не распознана, новость не берётся.

Как добавить источник — впишите строку по образцу.
Как убрать — удалите строку или поставьте # в начале.
"""

FEEDS = [
    # === Профильные ленты по ДЕТСКОЙ ЛИТЕРАТУРЕ (берём целиком) ===
    ("int", "The Guardian — детские книги", "https://www.theguardian.com/childrens-books-site/rss", "kids"),
    ("int", "Book Riot — детская литература", "https://bookriot.com/tag/childrens-books/feed/", "kids"),
    ("int", "A Fuse #8 (School Library Journal)", "https://afuse8production.slj.com/feed/", "kids"),

    # === Профильные ленты по МАРКЕТИНГУ КНИГ (берём целиком) ===
    ("int", "Jane Friedman", "https://janefriedman.com/feed/", "marketing"),
    ("int", "Written Word Media", "https://www.writtenwordmedia.com/feed/", "marketing"),
    ("int", "Publishing Perspectives", "https://publishingperspectives.com/feed/", "marketing"),

    # === Общие книжные ленты — тему определяем по ключевым словам ===
    # Зарубежные:
    ("int", "The Guardian Books", "https://www.theguardian.com/books/rss", None),
    ("int", "Literary Hub", "https://lithub.com/feed/", None),
    ("int", "Book Riot", "https://bookriot.com/feed/", None),
    ("int", "NYT Books", "https://rss.nytimes.com/services/xml/rss/nyt/Books.xml", None),
    ("int", "Publishers Weekly", "https://www.publishersweekly.com/pw/feeds/recent/index.xml", None),
    # Российские:
    ("ru", "Год Литературы", "https://godliteratury.ru/rss/", None),
    ("ru", "Лента.ру — Книги", "https://lenta.ru/rss/news/culture/books", None),
    ("ru", "Лента.ру — Культура", "https://lenta.ru/rss/news/culture", None),
    ("ru", "Коммерсантъ — Культура", "https://www.kommersant.ru/RSS/section-culture.xml", None),
    ("ru", "ТАСС", "https://tass.ru/rss/v2.xml", None),
    ("ru", "Российская газета", "https://rg.ru/xml/index.xml", None),
    ("ru", "Нож", "https://knife.media/feed/", None),
    ("ru", "Meduza", "https://meduza.io/rss/all", None),
]

# «Книжные» слова: для ОБЩИХ лент новость берём, только если она про книги
# (иначе «продажа билетов» или «войска продвигаются» попадут в маркетинг).
# Профильных лент это не касается — им доверяем по умолчанию.
BOOK_KEYWORDS = [
    "книг", "книж", "писател", "литератур", "роман", "издательств", "поэт",
    "поэзи", "бестселлер", "проза", "библиотек", "сказк", "букер", "нон-фикшн",
    "book", "novel", "author", "publish", "literary", "fiction", "memoir",
    "picture book", "reading",
]

# Ключевые слова темы «Детская литература».
KIDS_KEYWORDS = [
    # русские (совпадение по началу слова)
    "детск", "для детей", "подрост", "юношеск", "малыш", "дошкол", "сказк",
    "школьник", "книжка-картинка", "картонк", "иллюстрирова", "букварь",
    # английские
    "children", "kids", "kidlit", "picture book", "middle grade", "young adult",
    "teen", "toddler", "board book", "chapter book", "nursery", "kid lit",
]

# Ключевые слова темы «Маркетинг книг».
MARKETING_KEYWORDS = [
    # русские
    "маркетинг", "продвижени", "продвига", "продаж", "реклам", "аудитори",
    "бренд", "бестселлер", "тираж", "блогер", "соцсет", "пиар", "промо",
    "монетиз", "книжный рынок", "книготорг", "издательский бизнес", "продюсир",
    # английские
    "marketing", "promotion", "promote", "sales", "bestseller", "audience",
    "branding", "book launch", "booktok", "tiktok", "advertising", "publicity",
    "preorder", "pre-order", "backlist", "discoverability", "newsletter",
    "self-publish", "indie author", "royalties", "book sales", "book club",
]
