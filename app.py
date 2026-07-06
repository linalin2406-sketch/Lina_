# -*- coding: utf-8 -*-
"""
Главный файл портала. Запускает веб-сервер, отдаёт сайт и данные,
а также в фоне обновляет новости по расписанию.

Запуск:  python app.py
Затем откройте в браузере:  http://127.0.0.1:8000
"""

import asyncio
import contextlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import database
import fetcher

# Как часто автоматически обновлять новости (в минутах)
REFRESH_EVERY_MINUTES = 60

BASE_DIR = Path(__file__).parent


async def _refresh_loop():
    """Фоновая задача: обновляет новости при старте и затем по расписанию."""
    while True:
        try:
            report = await asyncio.to_thread(fetcher.fetch_all)
            print(f"[обновление] добавлено новых: {report['added']}, "
                  f"всего в базе: {report['total']}")
            if report["failed"]:
                print("[обновление] не ответили:", ", ".join(report["failed"]))
        except Exception as e:
            print("[обновление] ошибка:", e)
        await asyncio.sleep(REFRESH_EVERY_MINUTES * 60)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    task = asyncio.create_task(_refresh_loop())   # запустить фоновый сбор
    yield
    task.cancel()                                 # аккуратно остановить при выключении
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="Книжный портал", lifespan=lifespan)


@app.get("/api/news")
def api_news(topic: str = "", source: str = "", q: str = "", limit: int = 60):
    """Список новостей с фильтрами: тема (kids/marketing), источник, поиск."""
    return database.get_articles(
        topic=topic or None,
        source=source or None,
        query=q or None,
        limit=min(limit, 200),
    )


@app.get("/api/sources")
def api_sources(topic: str = ""):
    """Список источников для выпадающего фильтра."""
    return database.get_sources(topic=topic or None)


@app.get("/api/trends")
def api_trends(topic: str = ""):
    """Тренды — самые частые слова в свежих заголовках выбранной темы."""
    return fetcher.compute_trends(topic=topic or None)


@app.post("/api/refresh")
async def api_refresh():
    """Кнопка «Обновить сейчас» на сайте."""
    report = await asyncio.to_thread(fetcher.fetch_all)
    return JSONResponse(report)


@app.get("/api/stats")
def api_stats():
    return {"total": database.count_articles()}


# Отдаём сам сайт (index.html и статику) из папки static.
# Важно: этот пункт монтируется последним, чтобы не перехватывать /api/*
app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")


if __name__ == "__main__":
    import os
    import uvicorn
    # На своём компьютере — 127.0.0.1:8000.
    # В облаке (Render) переменные HOST/PORT задаются автоматически.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    if host == "127.0.0.1":
        print("Запускаю портал. Откройте в браузере:  http://127.0.0.1:8000")
    else:
        print(f"Запускаю портал в облаке на {host}:{port}")
    uvicorn.run(app, host=host, port=port)
