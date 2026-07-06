# -*- coding: utf-8 -*-
"""
Сборщик новостей: скачивает все RSS-ленты и складывает свежие записи в базу.
Также умеет считать «тренды» — самые частые слова в свежих заголовках.
"""

import re
import ssl
import html
import urllib.request
from datetime import datetime, timezone
from collections import Counter

import feedparser
import certifi

import database
from feeds import all_feeds, BOOK_KEYWORDS

# «Браузерный» User-Agent — некоторые сайты не отдают RSS стандартному агенту.
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
# Контекст SSL с актуальными сертификатами (решает CERTIFICATE_VERIFY_FAILED на macOS).
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _download(url, timeout=20):
    """Скачивает содержимое ленты сами, надёжно (SSL + User-Agent)."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
        return resp.read()


def _clean(text):
    """Убирает HTML-теги и лишние пробелы из текста."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)   # выкинуть теги
    text = html.unescape(text)             # &amp; -> &
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_about_books(title, summary):
    """
    True, если ЗАГОЛОВОК относится к книгам/литературе.
    Проверяем только заголовок (описание у больших лент часто содержит
    служебный текст и даёт ложные срабатывания) и требуем совпадения
    в начале слова (\\b), чтобы «роман» не ловило имя «Роман» в середине.
    """
    text = title.lower()
    return any(re.search(r"\b" + re.escape(kw), text) for kw in BOOK_KEYWORDS)


def _published_iso(entry):
    """Приводит дату публикации к сортируемой ISO-строке."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    # если даты нет — используем текущий момент, чтобы запись не «утонула»
    return datetime.now(timezone.utc).isoformat()


def fetch_all():
    """
    Проходит по всем лентам, сохраняет новые записи.
    Возвращает краткий отчёт: сколько добавлено и какие ленты не ответили.
    """
    database.init_db()
    now = datetime.now(timezone.utc).isoformat()
    added_total = 0
    failed = []

    for region, source, url, filter_books in all_feeds():
        try:
            raw = _download(url)              # скачиваем сами (надёжно)
            parsed = feedparser.parse(raw)    # затем разбираем содержимое
            if parsed.bozo and not parsed.entries:
                failed.append(source)
                continue
            for entry in parsed.entries:
                link = entry.get("link")
                title = _clean(entry.get("title"))
                if not link or not title:
                    continue
                summary = _clean(entry.get("summary", ""))
                # Для общих новостных лент оставляем только записи про книги
                if filter_books and not _is_about_books(title, summary):
                    continue
                article = {
                    "title": title,
                    "link": link,
                    "summary": summary[:600],
                    "published": _published_iso(entry),
                    "source": source,
                    "region": region,
                    "fetched_at": now,
                }
                if database.save_article(article):
                    added_total += 1
        except Exception:
            failed.append(source)

    return {"added": added_total, "failed": failed, "total": database.count_articles()}


# --- Тренды -----------------------------------------------------------------

# Слова, которые не считаем «трендом» (служебные/частые)
_STOPWORDS = set("""
и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по
только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли
если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя
книга книги книге книгу книг новая новый новые про для это этот эта эти года год
the a an of to in on for and or is are was as at by with from that this it its
book books new news read author story review best writer writers list our how
preview week weeks day days month july june fall spring winter summer shelftalker
edition guide top most about your you first year years time will can more into
""".split())


def compute_trends(region=None, limit=15):
    """
    Считает самые частые значимые слова в свежих заголовках —
    получается простой список «трендов» книжного рынка.
    """
    articles = database.get_articles(region=region, limit=200)
    counter = Counter()
    for a in articles:
        words = re.findall(r"[a-zA-Zа-яА-ЯёЁ]{4,}", a["title"].lower())
        for w in words:
            if w not in _STOPWORDS:
                counter[w] += 1
    return [{"word": w, "count": c} for w, c in counter.most_common(limit) if c > 1]


if __name__ == "__main__":
    # Позволяет запустить сбор вручную:  python fetcher.py
    print("Собираю новости из всех лент...")
    report = fetch_all()
    print(f"Добавлено новых: {report['added']}")
    print(f"Всего в базе:    {report['total']}")
    if report["failed"]:
        print("Не ответили ленты:", ", ".join(report["failed"]))
