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
from feeds import FEEDS, BOOK_KEYWORDS, KIDS_KEYWORDS, MARKETING_KEYWORDS

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
    """Убирает HTML-теги, служебные «хвосты» и лишние пробелы из текста."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)   # выкинуть теги
    text = html.unescape(text)             # &amp; -> &
    # Служебный «хвост» WordPress-лент: "The post ... appeared first on ..."
    text = re.sub(r"The post .*?appeared first on.*", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _count_hits(text, keywords):
    """Сколько ключевых слов темы встретилось в тексте (по началу слова)."""
    return sum(1 for kw in keywords if re.search(r"\b" + re.escape(kw), text))


def classify_topic(title, summary, default_topic):
    """
    Определяет тему новости: 'kids', 'marketing' или None (тема не распознана).

    Для профильных лент (default_topic задан) тему берём сразу — им доверяем.
    Для ОБЩИХ лент новость должна быть одновременно:
      1) про книги (есть «книжное» слово) — иначе это просто общая новость,
         где случайно встретилось «продажа» или «детский»;
      2) про одну из тем — тогда берём ту, где совпадений больше.
    Иначе возвращаем None (новость не берём).
    """
    if default_topic:
        return default_topic
    text = (title + " " + summary).lower()
    if not any(re.search(r"\b" + re.escape(kw), text) for kw in BOOK_KEYWORDS):
        return None
    kids = _count_hits(text, KIDS_KEYWORDS)
    mkt = _count_hits(text, MARKETING_KEYWORDS)
    if kids == 0 and mkt == 0:
        return None
    return "marketing" if mkt > kids else "kids"


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

    for region, source, url, default_topic in FEEDS:
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
                # Определяем тему; если не подходит ни под одну — пропускаем
                topic = classify_topic(title, summary, default_topic)
                if topic is None:
                    continue
                article = {
                    "title": title,
                    "link": link,
                    "summary": summary[:600],
                    "published": _published_iso(entry),
                    "source": source,
                    "topic": topic,
                    "region": region,
                    "fetched_at": now,
                }
                if database.save_article(article):
                    added_total += 1
        except Exception:
            failed.append(source)

    return {"added": added_total, "failed": failed, "total": database.count_articles()}


# --- Тренды -----------------------------------------------------------------

# Слова, которые не считаем «трендом» (служебные/частые, не несут темы)
_STOPWORDS = set("""
и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по
только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли
если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя
чтобы этот эта эти этого этому этих того тому тех свой свои своих весь всех всё
слово слова словах жизнь время времени после перед между через около над под без
дата дате проект который которые которых которого этой очень также тоже есть была
были стал стала может могут надо нужно дело лет год года году более менее самый
самая самые каждый каждая многие некоторые здесь тогда затем именно очень стало
книга книги книге книгу книг новая новый новые про для это как что где чем при
the a an of to in on for and or is are was as at by with from that this it its
book books new news read author story review best writer writers list our how
preview week weeks day days month july june fall spring winter summer shelftalker
edition guide top most about your you first year years time will can more into
some here there these those they them then than just like into out off been being
make makes made get got one two three five ten who which whom while what very much
many also such your our his her their its who whats has have had not but you can
back look looks where when were will would could should about over after before
still even only around this that here does dont into через один одна одно первый
well good part small silly working want need know says said just really things
""".split())


def compute_trends(topic=None, limit=15):
    """
    Считает «тренды» — самые частые значимые слова в свежих заголовках
    выбранной темы ('kids' или 'marketing').

    Чтобы одна повторяющаяся новость из одного источника не «забивала»
    тренды, настоящим трендом считаем только слово, которое встречается
    минимум у ДВУХ разных изданий. Если таких слов совсем мало (мало данных),
    мягко возвращаемся к обычному подсчёту по частоте.
    """
    articles = database.get_articles(topic=topic, limit=200)
    counter = Counter()          # сколько раз слово встретилось всего
    sources = {}                 # у скольких разных изданий встретилось слово
    for a in articles:
        text = (a["title"] + " " + (a["summary"] or "")).lower()
        seen = set()
        for w in re.findall(r"[a-zA-Zа-яА-ЯёЁ]{4,}", text):
            if w in _STOPWORDS:
                continue
            counter[w] += 1
            if w not in seen:            # каждую статью учитываем в «источниках» один раз
                sources.setdefault(w, set()).add(a["source"])
                seen.add(w)

    # Ранжируем по числу РАЗНЫХ изданий (чтобы повтор из одного источника
    # не всплывал), затем по общей частоте.
    ranked = sorted(
        counter.items(),
        key=lambda kv: (len(sources.get(kv[0], ())), kv[1]),
        reverse=True,
    )
    # Настоящий тренд — тема минимум у двух изданий
    multi = [(w, c) for w, c in ranked if len(sources.get(w, ())) >= 2]

    if len(multi) < 3:
        # Совсем мало данных — показываем самые частые слова (как запасной вариант)
        multi = [(w, c) for w, c in ranked if c > 1]

    return [{"word": w, "count": c} for w, c in multi[:limit]]


if __name__ == "__main__":
    # Позволяет запустить сбор вручную:  python fetcher.py
    print("Собираю новости из всех лент...")
    report = fetch_all()
    print(f"Добавлено новых: {report['added']}")
    print(f"Всего в базе:    {report['total']}")
    if report["failed"]:
        print("Не ответили ленты:", ", ".join(report["failed"]))
